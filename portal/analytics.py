"""Numbers for the progress charts: one pupil, one subject, and the whole school."""
import datetime
from collections import defaultdict

from .grading import BANDS, grade_for, total_of
from .models import (Attendance, ClassSubject, FeeInvoice, Payment, Score, Student, Term)


def term_sort_key(term):
    return (term.session, term.term_no)


def term_short(term):
    """'T1 25/26' for chart labels."""
    return "T%d %s/%s" % (term.term_no, term.session[2:4], term.session[7:9])


def term_end(term):
    """Roughly when a term ends. Used to count how many pupils the school had then."""
    year = int(term.session[:4])
    return {1: datetime.date(year, 12, 15),
            2: datetime.date(year + 1, 4, 10),
            3: datetime.date(year + 1, 7, 25)}[term.term_no]


def positions(pairs):
    """[(id, average), ...] -> {id: position}. Ties share a position."""
    result, last_avg, last_pos = {}, None, 0
    for index, (key, avg) in enumerate(sorted(pairs, key=lambda kv: -kv[1]), start=1):
        if last_avg is not None and round(avg, 2) == round(last_avg, 2):
            result[key] = last_pos
        else:
            result[key] = index
            last_pos = index
        last_avg = avg
    return result


def class_matrix(school_class):
    """({term_id: {student_id: {'average': x, 'complete': bool}}}, number of subjects)."""
    subject_ids = set(ClassSubject.objects.filter(school_class=school_class)
                      .values_list("subject_id", flat=True))
    needed = len(subject_ids)
    totals = defaultdict(lambda: defaultdict(list))
    rows = Score.objects.filter(student__school_class=school_class, student__user__is_active=True,
                                subject_id__in=subject_ids)
    for sid, term_id, ca1, ca2, exam in rows.values_list("student_id", "term_id", "ca1", "ca2", "exam"):
        total = total_of(ca1, ca2, exam)
        if total is not None:
            totals[term_id][sid].append(total)
    matrix = {}
    for term_id, per_student in totals.items():
        matrix[term_id] = {
            sid: {"average": sum(v) / len(v), "complete": needed > 0 and len(v) == needed}
            for sid, v in per_student.items()
        }
    return matrix, needed


def student_progress(student):
    """Term by term: the pupil's average, the class average and the position in class."""
    matrix, _ = class_matrix(student.school_class)
    terms = sorted(Term.objects.filter(id__in=list(matrix.keys())), key=term_sort_key)
    points = []
    for term in terms:
        per = matrix[term.id]
        mine = per.get(student.id)
        if mine is None:
            continue
        ranked = {sid: v["average"] for sid, v in per.items() if v["complete"]}
        pos = positions(list(ranked.items())) if mine["complete"] else {}
        points.append({
            "term_id": term.id, "label": term_short(term), "full_label": term.label(),
            "average": round(mine["average"], 1),
            "class_average": round(sum(v["average"] for v in per.values()) / len(per), 1),
            "position": pos.get(student.id), "ranked": len(ranked),
        })

    # each subject across the same terms
    by_subject = defaultdict(dict)
    rows = Score.objects.filter(student=student).select_related("subject")
    for sc in rows:
        total = total_of(sc.ca1, sc.ca2, sc.exam)
        if total is not None:
            by_subject[sc.subject.name][sc.term_id] = total
    subjects = [{"name": name, "values": [vals.get(p["term_id"]) for p in points]}
                for name, vals in sorted(by_subject.items())]

    change = None
    if len(points) >= 2:
        change = round(points[-1]["average"] - points[-2]["average"], 1)
    return {"points": points, "subjects": subjects, "change": change}


def subject_analytics(class_subject, term):
    """A teacher's view of one subject in one class: average by term and the grade spread now."""
    rows = Score.objects.filter(subject=class_subject.subject,
                                student__school_class=class_subject.school_class,
                                student__user__is_active=True).select_related("term")
    per_term = defaultdict(list)
    spread = {band[1]: 0 for band in BANDS}
    for sc in rows:
        total = total_of(sc.ca1, sc.ca2, sc.exam)
        if total is None:
            continue
        per_term[sc.term_id].append(total)
        if term is not None and sc.term_id == term.id:
            spread[grade_for(total)[0]] += 1
    terms = sorted(Term.objects.filter(id__in=list(per_term.keys())), key=term_sort_key)
    return {
        "trend": [{"label": term_short(t), "average": round(sum(per_term[t.id]) / len(per_term[t.id]), 1)}
                  for t in terms],
        "spread": [{"grade": g, "count": spread[g]} for g in [b[1] for b in BANDS]],
    }


def month_key(d):
    return d.strftime("%Y-%m")


def attendance_summary(student, months=6):
    """Overall rate, a monthly rate list, and the most recent days for one pupil."""
    today = datetime.date.today()
    since = today - datetime.timedelta(days=31 * months)
    records = list(Attendance.objects.filter(student=student, date__gte=since).order_by("date"))
    counts = {"present": 0, "late": 0, "absent": 0}
    monthly = defaultdict(lambda: [0, 0])          # month -> [attended, total]
    for r in records:
        counts[r.status] += 1
        monthly[month_key(r.date)][1] += 1
        if r.status != "absent":
            monthly[month_key(r.date)][0] += 1
    total = len(records)
    attended = counts["present"] + counts["late"]
    return {
        "rate": round(100 * attended / total, 1) if total else None,
        "present": counts["present"], "late": counts["late"], "absent": counts["absent"], "total": total,
        "months": [{"label": datetime.datetime.strptime(k, "%Y-%m").strftime("%b %y"),
                    "rate": round(100 * v[0] / v[1], 1)} for k, v in sorted(monthly.items())],
        "recent": [{"date": r.date.isoformat(), "label": r.date.strftime("%a %d %b"), "status": r.status}
                   for r in sorted(records, key=lambda r: r.date, reverse=True)[:14]],
    }


def school_analytics():
    """Everything the admin growth dashboard needs."""
    terms = sorted(Term.objects.all(), key=term_sort_key)
    term_by_id = {t.id: t for t in terms}

    totals_by_term = defaultdict(list)
    by_class_term = defaultdict(lambda: defaultdict(list))
    by_subject_term = defaultdict(lambda: defaultdict(list))
    student_term = defaultdict(lambda: defaultdict(list))      # term -> student -> totals
    rows = Score.objects.filter(student__user__is_active=True).select_related(
        "student__school_class", "student__user", "subject")
    for sc in rows:
        total = total_of(sc.ca1, sc.ca2, sc.exam)
        if total is None:
            continue
        totals_by_term[sc.term_id].append(total)
        by_class_term[sc.term_id][sc.student.school_class.name].append(total)
        by_subject_term[sc.term_id][sc.subject.name].append(total)
        student_term[sc.term_id][sc.student_id].append((total, sc.student))

    students = list(Student.objects.filter(user__is_active=True).select_related("user", "school_class"))

    trend = []
    for t in terms:
        totals = totals_by_term.get(t.id)
        if not totals:
            continue
        end = term_end(t)
        trend.append({
            "term_id": t.id, "label": term_short(t), "full_label": t.label(),
            "average": round(sum(totals) / len(totals), 1),
            "credit_rate": round(100 * sum(1 for x in totals if x >= 50) / len(totals), 1),
            "pass_rate": round(100 * sum(1 for x in totals if x >= 40) / len(totals), 1),
            "pupils": sum(1 for s in students if s.admitted_on <= end),
            "results": len(totals),
        })

    latest = None
    for t in reversed(terms):
        if totals_by_term.get(t.id):
            latest = t
            break
    previous = None
    if latest is not None:
        earlier = [t for t in terms if term_sort_key(t) < term_sort_key(latest) and totals_by_term.get(t.id)]
        previous = earlier[-1] if earlier else None

    classes, subjects, spread, top, support = [], [], {b[1]: 0 for b in BANDS}, [], []
    if latest is not None:
        for name, vals in sorted(by_class_term[latest.id].items()):
            classes.append({"name": name, "average": round(sum(vals) / len(vals), 1)})
        for name, vals in sorted(by_subject_term[latest.id].items()):
            now = sum(vals) / len(vals)
            before = None
            if previous is not None and by_subject_term[previous.id].get(name):
                pv = by_subject_term[previous.id][name]
                before = sum(pv) / len(pv)
            subjects.append({"name": name, "average": round(now, 1),
                             "change": None if before is None else round(now - before, 1)})
        for vals in totals_by_term[latest.id]:
            spread[grade_for(vals)[0]] += 1
        per_class = {}
        needed = {}
        for s in students:
            if s.school_class_id not in per_class:
                per_class[s.school_class_id] = ClassSubject.objects.filter(school_class=s.school_class).count()
            needed[s.id] = per_class[s.school_class_id]
        ranked = []
        for sid, pairs in student_term[latest.id].items():
            student = pairs[0][1]
            avg = sum(p[0] for p in pairs) / len(pairs)
            ranked.append({"id": sid, "name": student.user.get_full_name() or student.user.get_username(),
                           "class_name": student.school_class.name, "average": round(avg, 1),
                           "complete": len(pairs) == needed.get(sid, 0)})
        done = [r for r in ranked if r["complete"]]
        top = sorted(done, key=lambda r: -r["average"])[:5]
        support = sorted([r for r in done if r["average"] < 50], key=lambda r: r["average"])[:5]

    # attendance by month (all pupils)
    monthly = defaultdict(lambda: [0, 0])
    since = datetime.date.today() - datetime.timedelta(days=31 * 6)
    for d, status in Attendance.objects.filter(date__gte=since).values_list("date", "status"):
        monthly[month_key(d)][1] += 1
        if status != "absent":
            monthly[month_key(d)][0] += 1
    attendance = [{"label": datetime.datetime.strptime(k, "%Y-%m").strftime("%b %y"),
                   "rate": round(100 * v[0] / v[1], 1)} for k, v in sorted(monthly.items())]

    # fees by term
    billed, collected = defaultdict(int), defaultdict(int)
    for term_id, amount in FeeInvoice.objects.values_list("term_id", "amount"):
        billed[term_id] += amount
    for term_id, amount in Payment.objects.values_list("invoice__term_id", "amount"):
        collected[term_id] += amount
    fees = [{"label": term_short(t), "billed": billed[t.id], "collected": collected[t.id]}
            for t in terms if billed.get(t.id)]

    headline = None
    if latest is not None and trend:
        now_point = next(p for p in trend if p["term_id"] == latest.id)
        before_point = next((p for p in trend if previous and p["term_id"] == previous.id), None)
        headline = {
            "term": latest.label(), "average": now_point["average"],
            "change": None if before_point is None else round(now_point["average"] - before_point["average"], 1),
            "credit_rate": now_point["credit_rate"],
            "credit_change": None if before_point is None
            else round(now_point["credit_rate"] - before_point["credit_rate"], 1),
            "pupils": now_point["pupils"],
            "pupils_change": None if before_point is None else now_point["pupils"] - before_point["pupils"],
        }
    return {"headline": headline, "trend": trend, "classes": classes, "subjects": subjects,
            "spread": [{"grade": g, "count": spread[g]} for g in [b[1] for b in BANDS]],
            "top": top, "support": support, "attendance": attendance, "fees": fees}