"""Builds the numbers shown on result pages and report cards."""
from .grading import grade_for, total_of
from .models import ClassSubject, Remark, Score, Student, Term


def pick_term(requested_id=None):
    """The term asked for, else the current term, else the newest one."""
    if requested_id:
        term = Term.objects.filter(pk=requested_id).first()
        if term:
            return term
    return Term.objects.filter(is_current=True).first() or Term.objects.first()


def subject_rows(student, term):
    scores = {s.subject_id: s for s in Score.objects.filter(student=student, term=term)}
    assignments = (ClassSubject.objects.filter(school_class=student.school_class)
                   .select_related("subject", "teacher").order_by("subject__name"))
    rows = []
    for cs in assignments:
        sc = scores.get(cs.subject_id)
        ca1, ca2, exam = (sc.ca1, sc.ca2, sc.exam) if sc else (None, None, None)
        total = total_of(ca1, ca2, exam)
        grade, meaning = grade_for(total)
        rows.append({
            "subject_id": cs.subject_id,
            "subject": cs.subject.name,
            "teacher": (cs.teacher.get_full_name() or cs.teacher.get_username()) if cs.teacher else None,
            "ca1": ca1, "ca2": ca2, "exam": exam,
            "total": total, "grade": grade, "meaning": meaning,
        })
    return rows


def class_positions(school_class, term):
    """Position in class. Only students with every subject marked are ranked; ties share a position."""
    subject_count = ClassSubject.objects.filter(school_class=school_class).count()
    if subject_count == 0:
        return {}, 0
    students = list(Student.objects.filter(school_class=school_class, user__is_active=True))
    by_student = {}
    for sc in Score.objects.filter(student__in=students, term=term,
                                   subject__class_subjects__school_class=school_class):
        total = total_of(sc.ca1, sc.ca2, sc.exam)
        if total is not None:
            by_student.setdefault(sc.student_id, []).append(total)
    averages = {sid: sum(t) / len(t) for sid, t in by_student.items() if len(t) == subject_count}
    ordered = sorted(averages.items(), key=lambda kv: -kv[1])
    positions, last_avg, last_pos = {}, None, 0
    for index, (sid, avg) in enumerate(ordered, start=1):
        if last_avg is not None and round(avg, 2) == round(last_avg, 2):
            positions[sid] = last_pos
        else:
            positions[sid] = index
            last_pos = index
        last_avg = avg
    return positions, len(ordered)


def display_name(user):
    return user.get_full_name() or user.get_username()


def build_report(student, term, include_remarks=True):
    rows = subject_rows(student, term)
    done = [r["total"] for r in rows if r["total"] is not None]
    average = round(sum(done) / len(done), 1) if done else None
    overall_grade, overall_meaning = grade_for(average)
    positions, ranked = class_positions(student.school_class, term)

    remarks = []
    if include_remarks:
        for r in (Remark.objects.filter(student=student, term=term)
                  .select_related("teacher", "subject")):
            remarks.append({
                "id": r.id, "body": r.body,
                "teacher": display_name(r.teacher) if r.teacher else None,
                "subject": r.subject.name if r.subject else None,
                "date": r.created_at.strftime("%d %b %Y"),
            })

    return {
        "student": {"id": student.id, "name": display_name(student.user),
                    "class_name": student.school_class.name, "admission_no": student.admission_no,
                    "photo": (student.user.portal_profile.photo.url if getattr(student.user, "portal_profile", None) and student.user.portal_profile.photo else None)},
        "term": {"id": term.id, "label": term.label(), "is_current": term.is_current},
        "rows": rows,
        "subjects_total": len(rows),
        "subjects_done": len(done),
        "complete": bool(rows) and len(done) == len(rows),
        "average": average,
        "overall_grade": overall_grade,
        "overall_meaning": overall_meaning,
        "position": positions.get(student.id),
        "ranked": ranked,
        "remarks": remarks,
    }