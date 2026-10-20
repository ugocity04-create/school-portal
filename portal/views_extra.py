"""More of the JSON API: progress, attendance, notices, timetable, homework, fees, school dashboard."""
import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone

from . import analytics
from .models import (BREAK, DAYS, PERIODS, Announcement, Attendance, ClassSubject, Event, FeeInvoice,
                     Homework, Payment, SchoolClass, Student, Submission, Term, TimetableEntry)
from .permissions import can_view_student, role_of, students_of_class
from .reports import display_name, pick_term
from .views import api, error, int_or_none


def today():
    return timezone.localdate()


def visible_student(request, sid):
    """(student, None) or (None, error response)."""
    student = Student.objects.select_related("user", "school_class").filter(pk=sid).first()
    if student is None:
        return None, error("Not found.", 404)
    if not can_view_student(request.user, student):
        return None, error("You do not have access to this pupil.", 403)
    return student, None


def parse_date(text):
    try:
        return datetime.date.fromisoformat(str(text))
    except ValueError:
        return None


def naira_int(value):
    try:
        number = int(str(value).replace(",", "").strip())
    except ValueError:
        return None
    return number if number > 0 else None


# ------------------------------------------------------------------ progress charts

@api("student", "parent", "admin")
def student_progress(request, sid):
    student, bad = visible_student(request, sid)
    if bad:
        return bad
    return JsonResponse(analytics.student_progress(student))


@api("teacher")
def teacher_subject_analytics(request, cs_id):
    cs = get_object_or_404(ClassSubject.objects.select_related("school_class", "subject"), pk=cs_id)
    if cs.teacher_id != request.user.id:
        return error("This subject is not assigned to you.", 403)
    term = pick_term(int_or_none(request.GET.get("term")))
    return JsonResponse(analytics.subject_analytics(cs, term))


@api("admin")
def admin_analytics(request):
    return JsonResponse(analytics.school_analytics())


# ------------------------------------------------------------------ attendance

def _register(school_class, day, user_id=None):
    students = list(students_of_class(school_class))
    marks = {a.student_id: a.status for a in Attendance.objects.filter(student__in=students, date=day)}
    rows = [{"student_id": s.id, "name": display_name(s.user), "admission_no": s.admission_no,
             "status": marks.get(s.id)} for s in students]
    return {
        "class_name": school_class.name, "date": day.isoformat(),
        "label": day.strftime("%A %d %B %Y"), "weekend": day.weekday() > 4,
        "marked": bool(marks), "rows": rows,
    }


@api("teacher", methods=("GET", "POST"))
def teacher_attendance(request, class_id):
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    if not ClassSubject.objects.filter(school_class=school_class, teacher=request.user).exists():
        return error("You do not teach this class.", 403)

    if request.method == "POST":
        day = parse_date(request.data.get("date"))
        if day is None:
            return error("Choose a date.")
        if day > today():
            return error("You cannot take the register for a future date.")
        if (today() - day).days > 30:
            return error("The register for that date is closed. Ask the school office.")
        if day.weekday() > 4:
            return error("There is no school on weekends.")
        items = request.data.get("marks")
        if not isinstance(items, list):
            return error("No marks were sent.")
        allowed = {s.id for s in students_of_class(school_class)}
        clean = {}
        for item in items:
            sid = int_or_none(item.get("student_id")) if isinstance(item, dict) else None
            status = item.get("status") if isinstance(item, dict) else None
            if sid not in allowed or status not in ("present", "absent", "late"):
                return error("Something in the register is not valid.")
            clean[sid] = status
        with transaction.atomic():
            for sid, status in clean.items():
                Attendance.objects.update_or_create(
                    student_id=sid, date=day, defaults={"status": status, "marked_by": request.user})
        data = _register(school_class, day)
        data["saved"] = True
        return JsonResponse(data)

    day = parse_date(request.GET.get("date")) or today()
    return JsonResponse(_register(school_class, day))


@api("student", "parent", "admin")
def student_attendance(request, sid):
    student, bad = visible_student(request, sid)
    if bad:
        return bad
    return JsonResponse(analytics.attendance_summary(student))


# ------------------------------------------------------------------ notices and events

def _audiences(role):
    return {"student": ["all", "students"], "parent": ["all", "parents"],
            "teacher": ["all", "teachers"]}.get(role, ["all", "students", "parents", "teachers"])


def _notice_payload(a):
    return {"id": a.id, "title": a.title, "body": a.body, "audience": a.audience, "pinned": a.pinned,
            "date": a.created_at.strftime("%d %b %Y"),
            "by": display_name(a.created_by) if a.created_by else "School office"}


def _event_payload(e):
    return {"id": e.id, "title": e.title, "description": e.description, "date": e.date.isoformat(),
            "label": e.date.strftime("%a %d %b") + (" to " + e.end_date.strftime("%a %d %b") if e.end_date else ""),
            "days_away": (e.date - today()).days}


@api()
def notices(request):
    items = Announcement.objects.filter(audience__in=_audiences(role_of(request.user))).select_related("created_by")[:12]
    events = Event.objects.filter(date__gte=today())[:6]
    return JsonResponse({"announcements": [_notice_payload(a) for a in items],
                         "events": [_event_payload(e) for e in events]})


@api("admin", methods=("POST",))
def admin_notice_create(request):
    title = " ".join(str(request.data.get("title", "")).split())
    body = str(request.data.get("body", "")).strip()
    audience = request.data.get("audience", "all")
    if len(title) < 3 or len(title) > 120:
        return error("Give the notice a title (3 to 120 characters).")
    if len(body) < 3 or len(body) > 1000:
        return error("Write the notice (up to 1000 characters).")
    if audience not in ("all", "students", "parents", "teachers"):
        return error("Choose who should see it.")
    Announcement.objects.create(title=title, body=body, audience=audience,
                                pinned=bool(request.data.get("pinned")), created_by=request.user)
    return JsonResponse({"ok": True})


@api("admin", methods=("POST",))
def admin_notice_delete(request, nid):
    get_object_or_404(Announcement, pk=nid).delete()
    return JsonResponse({"ok": True})


@api("admin", methods=("POST",))
def admin_event_create(request):
    title = " ".join(str(request.data.get("title", "")).split())
    day = parse_date(request.data.get("date"))
    end = parse_date(request.data.get("end_date")) if request.data.get("end_date") else None
    if len(title) < 3 or len(title) > 120:
        return error("Give the event a title (3 to 120 characters).")
    if day is None:
        return error("Choose the date.")
    if end is not None and end < day:
        return error("The end date is before the start date.")
    Event.objects.create(title=title, date=day, end_date=end,
                         description=str(request.data.get("description", ""))[:240])
    return JsonResponse({"ok": True})


@api("admin", methods=("POST",))
def admin_event_delete(request, eid):
    get_object_or_404(Event, pk=eid).delete()
    return JsonResponse({"ok": True})


@api("admin")
def admin_notice_list(request):
    return JsonResponse({
        "announcements": [_notice_payload(a) for a in Announcement.objects.select_related("created_by")[:30]],
        "events": [_event_payload(e) for e in Event.objects.filter(date__gte=today())[:30]],
    })


# ------------------------------------------------------------------ timetable

def _timetable_rows(cell_for):
    """Build the grid. cell_for(day, period) returns a dict or None."""
    rows = []
    for no, start, end in PERIODS:
        if no == 5:
            rows.append({"break": True, "label": "%s to %s" % BREAK})
        rows.append({"period": no, "label": "%s to %s" % (start, end),
                     "cells": [cell_for(d, no) for d in range(len(DAYS))]})
    return {"days": DAYS, "rows": rows}


@api("student", "parent", "admin")
def student_timetable(request, sid):
    student, bad = visible_student(request, sid)
    if bad:
        return bad
    teachers = {cs.subject_id: display_name(cs.teacher) if cs.teacher else None
                for cs in ClassSubject.objects.filter(school_class=student.school_class).select_related("teacher")}
    grid = {(e.day, e.period): e for e in
            TimetableEntry.objects.filter(school_class=student.school_class).select_related("subject")}

    def cell(day, period):
        e = grid.get((day, period))
        return None if e is None else {"subject": e.subject.name, "teacher": teachers.get(e.subject_id)}

    data = _timetable_rows(cell)
    data["class_name"] = student.school_class.name
    return JsonResponse(data)


@api("teacher")
def teacher_timetable(request):
    mine = {(cs.school_class_id, cs.subject_id): cs for cs in
            ClassSubject.objects.filter(teacher=request.user)}
    grid = {}
    entries = TimetableEntry.objects.filter(
        school_class_id__in=[k[0] for k in mine]).select_related("subject", "school_class")
    for e in entries:
        if (e.school_class_id, e.subject_id) in mine:
            grid[(e.day, e.period)] = e

    def cell(day, period):
        e = grid.get((day, period))
        return None if e is None else {"subject": e.subject.name, "teacher": e.school_class.name}

    return JsonResponse(_timetable_rows(cell))


# ------------------------------------------------------------------ homework

def _sub_payload(sub):
    if sub is None:
        return None
    return {"answer": sub.answer, "late": sub.late,
            "submitted_at": timezone.localtime(sub.submitted_at).strftime("%d %b %Y, %I:%M %p"),
            "score": None if sub.score is None else float(sub.score),
            "feedback": sub.feedback, "graded": sub.graded_at is not None}


def _homework_payload(h, sub=None, with_status=False):
    days = (h.due_date - today()).days
    out = {"id": h.id, "title": h.title, "description": h.description,
           "subject": h.class_subject.subject.name, "class_name": h.class_subject.school_class.name,
           "mode": h.mode, "max_score": h.max_score,
           "due": h.due_date.isoformat(), "due_label": h.due_date.strftime("%a %d %b"),
           "days_left": days, "overdue": days < 0}
    if with_status:
        if h.mode == "online":
            out["status"] = ("graded" if sub is not None and sub.graded_at else
                             "submitted" if sub is not None else "todo")
            out["score"] = None if sub is None or sub.score is None else float(sub.score)
        else:
            out["status"] = "notebook"
    return out


@api("student", "parent", "admin")
def student_homework(request, sid):
    student, bad = visible_student(request, sid)
    if bad:
        return bad
    items = list(Homework.objects.filter(class_subject__school_class=student.school_class)
                 .select_related("class_subject__subject", "class_subject__school_class"))
    subs = {s.homework_id: s for s in Submission.objects.filter(student=student, homework__in=items)}

    def row(h):
        return _homework_payload(h, subs.get(h.id), with_status=True)

    upcoming = [row(h) for h in items if h.due_date >= today()]
    recent = [row(h) for h in items if h.due_date < today() and (today() - h.due_date).days <= 14]
    return JsonResponse({"upcoming": upcoming, "recent": sorted(recent, key=lambda h: h["due"], reverse=True)})


@api("student", "parent", "admin")
def student_homework_detail(request, sid, hid):
    student, bad = visible_student(request, sid)
    if bad:
        return bad
    h = get_object_or_404(Homework.objects.select_related("class_subject__subject", "class_subject__school_class",
                                                         "class_subject__teacher"),
                          pk=hid, class_subject__school_class=student.school_class)
    sub = Submission.objects.filter(homework=h, student=student).first()
    data = _homework_payload(h, sub, with_status=True)
    data["instructions"] = h.instructions or h.description
    data["teacher"] = display_name(h.class_subject.teacher) if h.class_subject.teacher else None
    data["submission"] = _sub_payload(sub)
    data["can_submit"] = (role_of(request.user) == "student" and h.mode == "online"
                          and not (sub is not None and sub.graded_at))
    data["student_name"] = display_name(student.user)
    return JsonResponse(data)


@api("student", methods=("POST",))
def student_homework_submit(request, sid, hid):
    student, bad = visible_student(request, sid)
    if bad:
        return bad
    if role_of(request.user) != "student":
        return error("Only the pupil can hand in their own work.", 403)
    h = get_object_or_404(Homework, pk=hid, class_subject__school_class=student.school_class)
    if h.mode != "online":
        return error("This homework is done in the notebook, so there is nothing to hand in here.")
    answer = str(request.data.get("answer", "")).strip()
    if len(answer) < 2:
        return error("Write your answer before you hand in.")
    if len(answer) > 8000:
        return error("That answer is too long (8000 characters at most).")
    sub = Submission.objects.filter(homework=h, student=student).first()
    if sub is not None and sub.graded_at:
        return error("This work has already been marked, so it can no longer be changed.")
    late = today() > h.due_date
    if sub is None:
        sub = Submission(homework=h, student=student)
    sub.answer, sub.late = answer, late
    sub.save()
    return JsonResponse({"submission": _sub_payload(sub)})


@api("teacher", methods=("GET", "POST"))
def teacher_homework(request, cs_id):
    cs = get_object_or_404(ClassSubject.objects.select_related("school_class", "subject"), pk=cs_id)
    if cs.teacher_id != request.user.id:
        return error("This subject is not assigned to you.", 403)
    if request.method == "POST":
        title = " ".join(str(request.data.get("title", "")).split())
        due = parse_date(request.data.get("due_date"))
        mode = request.data.get("mode", "notebook")
        if len(title) < 3 or len(title) > 120:
            return error("Give the homework a title (3 to 120 characters).")
        if due is None or due < today():
            return error("Choose a due date that is today or later.")
        if mode not in ("notebook", "online"):
            return error("Choose where the work is done: notebook or online.")
        instructions = str(request.data.get("instructions", "")).strip()[:4000]
        if len(instructions) < 5:
            return error("Write what the pupils must do (at least a short sentence).")
        max_score = int_or_none(request.data.get("max_score")) or 10
        if not 1 <= max_score <= 100:
            return error("Marks must be between 1 and 100.")
        Homework.objects.create(class_subject=cs, title=title, due_date=due, mode=mode,
                                instructions=instructions, max_score=max_score,
                                description=" ".join(instructions.split())[:140])
    items = list(cs.homework.select_related("class_subject__subject", "class_subject__school_class")
                 .order_by("-due_date")[:30])
    pupils = students_of_class(cs.school_class).count()
    counts = {}
    for sub in Submission.objects.filter(homework__in=items):
        c = counts.setdefault(sub.homework_id, [0, 0])
        c[0] += 1
        c[1] += 1 if sub.graded_at else 0
    rows = []
    for h in items:
        p = _homework_payload(h)
        c = counts.get(h.id, [0, 0])
        p.update({"submitted": c[0], "graded": c[1], "pupils": pupils})
        rows.append(p)
    return JsonResponse({"assignment": {"id": cs.id, "class_name": cs.school_class.name, "subject": cs.subject.name},
                         "homework": rows})


def _own_homework(request, hid):
    h = get_object_or_404(Homework.objects.select_related("class_subject__subject", "class_subject__school_class"),
                          pk=hid)
    if h.class_subject.teacher_id != request.user.id:
        return None, error("This homework is not yours.", 403)
    return h, None


@api("teacher")
def teacher_submissions(request, hid):
    h, bad = _own_homework(request, hid)
    if bad:
        return bad
    subs = {s.student_id: s for s in h.submissions.all()}
    rows = []
    for st in students_of_class(h.class_subject.school_class):
        rows.append({"student_id": st.id, "name": display_name(st.user), "admission_no": st.admission_no,
                     "submission": _sub_payload(subs.get(st.id))})
    head = _homework_payload(h)
    head["instructions"] = h.instructions or h.description
    return JsonResponse({"homework": head, "rows": rows})


@api("teacher", methods=("POST",))
def teacher_grade(request, hid, sid):
    h, bad = _own_homework(request, hid)
    if bad:
        return bad
    sub = get_object_or_404(Submission, homework=h, student_id=sid)
    try:
        score = float(request.data.get("score"))
    except (TypeError, ValueError):
        return error("Enter a mark as a number.")
    if not 0 <= score <= h.max_score:
        return error("The mark must be between 0 and %d." % h.max_score)
    sub.score = round(score, 1)
    sub.feedback = str(request.data.get("feedback", "")).strip()[:1000]
    sub.graded_at = timezone.now()
    sub.save()
    return JsonResponse({"submission": _sub_payload(sub)})


@api("teacher", methods=("POST",))
def teacher_homework_delete(request, hid):
    h = get_object_or_404(Homework.objects.select_related("class_subject"), pk=hid)
    if h.class_subject.teacher_id != request.user.id:
        return error("This homework is not yours.", 403)
    h.delete()
    return JsonResponse({"ok": True})


# ------------------------------------------------------------------ fees

def _invoice_payload(inv):
    payments = list(inv.payments.all())
    paid = sum(p.amount for p in payments)
    return {
        "id": inv.id, "title": inv.title, "term": inv.term.label(), "amount": inv.amount,
        "paid": paid, "balance": inv.amount - paid,
        "status": "paid" if paid >= inv.amount else ("part" if paid > 0 else "unpaid"),
        "payments": [{"id": p.id, "amount": p.amount, "date": p.paid_on.strftime("%d %b %Y"),
                      "method": p.get_method_display(), "reference": p.reference} for p in payments],
    }


@api("parent", "admin")
def student_fees(request, sid):
    student, bad = visible_student(request, sid)
    if bad:
        return bad
    invoices = [_invoice_payload(i) for i in
                FeeInvoice.objects.filter(student=student).select_related("term").prefetch_related("payments")]
    return JsonResponse({
        "invoices": invoices,
        "billed": sum(i["amount"] for i in invoices),
        "paid": sum(i["paid"] for i in invoices),
        "balance": sum(i["balance"] for i in invoices),
    })


@api("parent", "admin")
def payment_receipt(request, pid):
    p = get_object_or_404(Payment.objects.select_related("invoice__student__user", "invoice__student__school_class",
                                                         "invoice__term", "recorded_by"), pk=pid)
    student = p.invoice.student
    if not can_view_student(request.user, student):
        return error("You do not have access to this receipt.", 403)
    inv = p.invoice
    return JsonResponse({
        "receipt_no": "GA-%06d" % p.id, "amount": p.amount, "date": p.paid_on.strftime("%d %B %Y"),
        "method": p.get_method_display(), "reference": p.reference,
        "student": {"id": student.id, "name": display_name(student.user),
                    "class_name": student.school_class.name, "admission_no": student.admission_no},
        "invoice": {"title": inv.title, "term": inv.term.label(), "amount": inv.amount,
                    "paid": inv.paid(), "balance": inv.balance()},
        "recorded_by": display_name(p.recorded_by) if p.recorded_by else "School office",
    })


@api("admin")
def admin_fees(request):
    term = pick_term(int_or_none(request.GET.get("term")))
    if term is None:
        return JsonResponse({"term": None, "classes": [], "outstanding": [], "totals": {}, "school_classes": []})
    invoices = list(FeeInvoice.objects.filter(term=term, student__user__is_active=True)
                    .select_related("student__user", "student__school_class", "term")
                    .prefetch_related("payments"))
    by_class, outstanding = {}, []
    for inv in invoices:
        name = inv.student.school_class.name
        row = by_class.setdefault(name, {"name": name, "billed": 0, "collected": 0})
        paid = inv.paid()
        row["billed"] += inv.amount
        row["collected"] += paid
        if inv.amount - paid > 0:
            outstanding.append({"invoice_id": inv.id, "student": display_name(inv.student.user),
                                "student_id": inv.student_id, "class_name": name, "title": inv.title,
                                "balance": inv.amount - paid, "amount": inv.amount})
    outstanding.sort(key=lambda r: -r["balance"])
    billed = sum(i.amount for i in invoices)
    collected = sum(r["collected"] for r in by_class.values())
    return JsonResponse({
        "term": term.label(),
        "totals": {"billed": billed, "collected": collected, "outstanding": billed - collected,
                   "rate": round(100 * collected / billed, 1) if billed else None},
        "classes": sorted(by_class.values(), key=lambda r: r["name"]),
        "outstanding": outstanding[:60],
        "school_classes": [{"id": c.id, "name": c.name} for c in SchoolClass.objects.all()],
    })


@api("admin", methods=("POST",))
def admin_record_payment(request):
    inv = FeeInvoice.objects.filter(pk=int_or_none(request.data.get("invoice_id"))).first()
    if inv is None:
        return error("Choose an invoice.")
    amount = naira_int(request.data.get("amount"))
    if amount is None:
        return error("Enter the amount in naira, for example 25000.")
    if amount > inv.balance():
        return error("That is more than the balance owed (%s)." % inv.balance())
    method = request.data.get("method", "transfer")
    if method not in ("cash", "transfer", "pos", "online"):
        return error("Choose how it was paid.")
    payment = Payment.objects.create(invoice=inv, amount=amount, method=method, paid_on=today(),
                                     reference=str(request.data.get("reference", "")).strip()[:40],
                                     recorded_by=request.user)
    return JsonResponse({"ok": True, "payment_id": payment.id})


@api("admin", methods=("POST",))
def admin_generate_invoices(request):
    """Bill every active pupil (or one class) for the current term."""
    term = Term.objects.filter(is_current=True).first()
    if term is None:
        return error("Set a current term first.")
    title = " ".join(str(request.data.get("title", "School fees")).split())[:80]
    amount = naira_int(request.data.get("amount"))
    if len(title) < 3:
        return error("Give the charge a name, for example School fees.")
    if amount is None:
        return error("Enter the amount in naira, for example 85000.")
    students = Student.objects.filter(user__is_active=True)
    class_id = int_or_none(request.data.get("class_id"))
    if class_id:
        students = students.filter(school_class_id=class_id)
    made = 0
    for s in students:
        _, created = FeeInvoice.objects.get_or_create(student=s, term=term, title=title,
                                                      defaults={"amount": amount})
        made += 1 if created else 0
    return JsonResponse({"ok": True, "created": made})


# ---------------------------------------------------------------- profile photo
import os as _os
import uuid as _uuid
from django.views.decorators.http import require_http_methods as _rhm

_PHOTO_TYPES = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
}


def _photo_ext(head):
    for sig, ext in _PHOTO_TYPES.items():
        if head.startswith(sig):
            return ext
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


@_rhm(["POST", "DELETE"])
def my_photo(request):
    """Upload (POST, field 'photo') or remove (DELETE) your own profile picture."""
    from django.http import JsonResponse
    from .models import Profile
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Please sign in."}, status=401)
    profile, _ = Profile.objects.get_or_create(user=request.user)

    def drop_old():
        if profile.photo:
            try:
                profile.photo.delete(save=False)
            except OSError:
                pass

    if request.method == "DELETE":
        drop_old()
        profile.photo = ""
        profile.save()
        return JsonResponse({"photo": None})

    f = request.FILES.get("photo")
    if not f:
        return JsonResponse({"error": "Choose a picture first."}, status=400)
    if f.size > 2 * 1024 * 1024:
        return JsonResponse({"error": "That picture is too big. Use one under 2 MB."}, status=400)
    ext = _photo_ext(f.read(16))
    f.seek(0)
    if not ext:
        return JsonResponse({"error": "Use a JPG, PNG or WEBP picture."}, status=400)
    drop_old()
    f.name = "u%s-%s.%s" % (request.user.id, _uuid.uuid4().hex[:10], ext)
    profile.photo = f
    profile.save()
    return JsonResponse({"photo": profile.photo.url})