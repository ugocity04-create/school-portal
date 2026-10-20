"""The JSON API the React frontend talks to. Plain Django, no extra packages."""
import json
from functools import wraps

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie

from .grading import MAX_CA1, MAX_CA2, MAX_EXAM, grade_for, parse_score, total_of
from .models import ClassSubject, ParentLink, Remark, Score, Student, Subject, Term
from .permissions import can_view_student, role_of, students_of_class, teacher_teaches_student
from .reports import build_report, display_name, pick_term

MAX_FAILS = 5
LOCK_SECONDS = 600


# ------------------------------------------------------------------ helpers

def error(message, status=400, **extra):
    return JsonResponse({"error": message, **extra}, status=status)


def api(*roles, methods=("GET",)):
    """Check method, sign-in and role, read the JSON body, and never let the browser cache the answer."""
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.method not in methods:
                return error("Method not allowed.", 405)
            if not request.user.is_authenticated:
                return error("Please sign in.", 401)
            if roles and role_of(request.user) not in roles:
                return error("You do not have access to this.", 403)
            request.data = {}
            if request.method in ("POST", "PUT", "PATCH") and request.body:
                try:
                    request.data = json.loads(request.body.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    return error("That request could not be read.")
                if not isinstance(request.data, dict):
                    return error("That request could not be read.")
            try:
                response = view(request, *args, **kwargs)
            except Http404:
                return error("Not found.", 404)
            response["Cache-Control"] = "no-store"
            return response
        return wrapper
    return decorator


def photo_url(user):
    p = getattr(user, "portal_profile", None)
    return p.photo.url if p and p.photo else None


def user_payload(user):
    return {"id": user.id, "username": user.get_username(), "name": display_name(user),
            "role": role_of(user), "photo": photo_url(user)}


def int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ sign in

@ensure_csrf_cookie
def me(request):
    """Who is signed in. Also hands the browser its CSRF cookie."""
    if not request.user.is_authenticated:
        return JsonResponse({"user": None})
    return JsonResponse({"user": user_payload(request.user)})


def _client_ip(request):
    return request.META.get("REMOTE_ADDR", "unknown")


def login_view(request):
    if request.method != "POST":
        return error("Method not allowed.", 405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        username = str(data.get("username", "")).strip().lower()[:150]
        password = str(data.get("password", ""))
    except (ValueError, AttributeError, UnicodeDecodeError):
        return error("That request could not be read.")

    user_key = "fails:user:%s" % username
    ip_key = "fails:ip:%s" % _client_ip(request)
    if cache.get(user_key, 0) >= MAX_FAILS or cache.get(ip_key, 0) >= MAX_FAILS * 6:
        return error("Too many wrong tries. Please wait ten minutes and try again.", 429)

    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        for key in (user_key, ip_key):
            cache.set(key, cache.get(key, 0) + 1, LOCK_SECONDS)
        return error("Wrong username or password.", 400)

    cache.delete(user_key)
    login(request, user)
    return JsonResponse({"user": user_payload(user)})


def logout_view(request):
    if request.method != "POST":
        return error("Method not allowed.", 405)
    logout(request)
    return JsonResponse({"ok": True})


@api(methods=("POST",))
def change_password(request):
    old = str(request.data.get("old_password", ""))
    new = str(request.data.get("new_password", ""))
    if not request.user.check_password(old):
        return error("Your current password is not right.")
    try:
        validate_password(new, request.user)
    except ValidationError as exc:
        return error(" ".join(exc.messages))
    request.user.set_password(new)
    request.user.save()
    update_session_auth_hash(request, request.user)   # stay signed in
    return JsonResponse({"ok": True})


# ------------------------------------------------------------------ results (student, parent, admin)

@api()
def terms(request):
    return JsonResponse({"terms": [{"id": t.id, "label": t.label(), "is_current": t.is_current}
                                   for t in Term.objects.all()]})


def _show_remarks(user):
    from django.conf import settings
    if role_of(user) == "student":
        return getattr(settings, "STUDENTS_SEE_REMARKS", True)
    return True


@api("student")
def my_student(request):
    student = get_object_or_404(Student, user=request.user)
    return JsonResponse({"student_id": student.id})


@api("parent")
def my_children(request):
    term = pick_term(int_or_none(request.GET.get("term")))
    cards = []
    links = ParentLink.objects.filter(parent=request.user, student__user__is_active=True) \
        .select_related("student__user", "student__school_class")
    for link in links:
        student = link.student
        report = build_report(student, term, include_remarks=True) if term else None
        cards.append({
            "id": student.id, "name": display_name(student.user),
            "class_name": student.school_class.name, "admission_no": student.admission_no,
            "average": report["average"] if report else None,
            "position": report["position"] if report else None,
            "ranked": report["ranked"] if report else 0,
            "complete": report["complete"] if report else False,
            "subjects_done": report["subjects_done"] if report else 0,
            "subjects_total": report["subjects_total"] if report else 0,
            "remark_count": len(report["remarks"]) if report else 0,
        })
    return JsonResponse({"children": cards, "term": term.label() if term else None})


@api("student", "parent", "admin")
def student_report(request, sid):
    student = get_object_or_404(Student.objects.select_related("user", "school_class"), pk=sid)
    if not can_view_student(request.user, student):
        return error("You do not have access to this pupil.", 403)
    term = pick_term(int_or_none(request.GET.get("term")))
    if term is None:
        return error("No term has been set up yet.", 404)
    return JsonResponse(build_report(student, term, include_remarks=_show_remarks(request.user)))


# ------------------------------------------------------------------ teachers

def _assignment_for(user, cs_id):
    cs = get_object_or_404(ClassSubject.objects.select_related("school_class", "subject"), pk=cs_id)
    if cs.teacher_id != user.id:
        raise PermissionError
    return cs


@api("teacher")
def teacher_assignments(request):
    term = pick_term()
    out = []
    qs = ClassSubject.objects.filter(teacher=request.user).select_related("school_class", "subject")
    for cs in qs:
        pupils = Student.objects.filter(school_class=cs.school_class, user__is_active=True).count()
        done = 0
        if term:
            done = Score.objects.filter(
                term=term, subject=cs.subject, student__school_class=cs.school_class,
                student__user__is_active=True, ca1__isnull=False, ca2__isnull=False, exam__isnull=False,
            ).count()
        out.append({"id": cs.id, "class_id": cs.school_class_id, "class_name": cs.school_class.name,
                    "subject": cs.subject.name, "pupils": pupils, "complete": done})
    return JsonResponse({"assignments": out, "term": term.label() if term else None})


@api("teacher", methods=("GET", "POST"))
def teacher_scores(request, cs_id):
    try:
        cs = _assignment_for(request.user, cs_id)
    except PermissionError:
        return error("This subject is not assigned to you.", 403)
    students = list(students_of_class(cs.school_class))

    if request.method == "POST":
        term = Term.objects.filter(pk=int_or_none(request.data.get("term_id"))).first()
        if term is None:
            return error("Choose a term.")
        if not term.is_current:
            return error("This is a past term, so scores are view-only.", 403)
        items = request.data.get("scores")
        if not isinstance(items, list):
            return error("No scores were sent.")
        allowed = {s.id: s for s in students}
        parsed, problems = {}, {}
        for item in items:
            sid = int_or_none(item.get("student_id")) if isinstance(item, dict) else None
            if sid not in allowed:
                return error("A pupil in the list is not in this class.")
            values, errs = {}, {}
            for field, maximum in (("ca1", MAX_CA1), ("ca2", MAX_CA2), ("exam", MAX_EXAM)):
                value, err = parse_score(item.get(field), maximum)
                values[field] = value
                if err:
                    errs[field] = err
            parsed[sid] = values
            if errs:
                problems[sid] = errs
        if problems:
            return error("Some scores are not valid. Nothing was saved.", 400, problems=problems)
        with transaction.atomic():
            for sid, v in parsed.items():
                existing = Score.objects.filter(student_id=sid, subject=cs.subject, term=term).first()
                if existing is None and all(x is None for x in v.values()):
                    continue
                Score.objects.update_or_create(
                    student_id=sid, subject=cs.subject, term=term,
                    defaults={"ca1": v["ca1"], "ca2": v["ca2"], "exam": v["exam"],
                              "updated_by": request.user})
        # fall through and return the fresh table

    term = pick_term(int_or_none(request.GET.get("term") or request.data.get("term_id")))
    existing = {s.student_id: s for s in Score.objects.filter(subject=cs.subject, term=term)}
    rows = []
    for st in students:
        sc = existing.get(st.id)
        total = total_of(sc.ca1, sc.ca2, sc.exam) if sc else None
        grade, _ = grade_for(total)
        rows.append({"student_id": st.id, "name": display_name(st.user), "admission_no": st.admission_no,
                     "ca1": sc.ca1 if sc else None, "ca2": sc.ca2 if sc else None,
                     "exam": sc.exam if sc else None, "total": total, "grade": grade})
    return JsonResponse({
        "assignment": {"id": cs.id, "class_name": cs.school_class.name, "subject": cs.subject.name},
        "term": {"id": term.id, "label": term.label(), "is_current": term.is_current},
        "editable": term.is_current,
        "maxes": {"ca1": MAX_CA1, "ca2": MAX_CA2, "exam": MAX_EXAM},
        "rows": rows, "saved": request.method == "POST",
    })


@api("teacher")
def teacher_class_students(request, class_id):
    link = (ClassSubject.objects.filter(school_class_id=class_id, teacher=request.user)
            .select_related("school_class").first())
    if link is None:
        return error("You do not teach this class.", 403)
    klass = link
    pupils = [{"id": s.id, "name": display_name(s.user), "admission_no": s.admission_no}
              for s in students_of_class(klass.school_class)]
    return JsonResponse({"class_name": klass.school_class.name, "students": pupils})


@api("teacher", methods=("GET", "POST"))
def teacher_remarks(request, sid):
    student = get_object_or_404(Student.objects.select_related("user", "school_class"), pk=sid)
    if not teacher_teaches_student(request.user, student):
        return error("You do not teach this pupil.", 403)
    my_subjects = list(Subject.objects.filter(
        class_subjects__school_class=student.school_class, class_subjects__teacher=request.user))
    term = pick_term()

    if request.method == "POST":
        body = " ".join(str(request.data.get("body", "")).split())
        subject_id = int_or_none(request.data.get("subject_id"))
        if term is None:
            return error("No term has been set up yet.")
        if len(body) < 3:
            return error("Write a remark of at least a few words.")
        if len(body) > 600:
            return error("Please keep the remark under 600 characters.")
        if subject_id and subject_id not in [s.id for s in my_subjects]:
            return error("You can only link a remark to a subject you teach this class.")
        Remark.objects.create(student=student, term=term, teacher=request.user,
                              subject_id=subject_id or None, body=body)

    mine = Remark.objects.filter(student=student, teacher=request.user) \
        .select_related("subject", "term")
    return JsonResponse({
        "student": {"id": student.id, "name": display_name(student.user),
                    "class_name": student.school_class.name, "class_id": student.school_class_id},
        "term": term.label() if term else None,
        "subjects": [{"id": s.id, "name": s.name} for s in my_subjects],
        "remarks": [{"id": r.id, "body": r.body, "subject": r.subject.name if r.subject else None,
                     "term": r.term.label(), "date": r.created_at.strftime("%d %b %Y")} for r in mine],
    })


@api("teacher", methods=("POST",))
def teacher_remark_delete(request, rid):
    remark = get_object_or_404(Remark, pk=rid, teacher=request.user)
    remark.delete()
    return JsonResponse({"ok": True})


# ------------------------------------------------------------------ admin overview

@api("admin")
def admin_overview(request):
  from django.contrib.auth import get_user_model
  from .models import SchoolClass
  User = get_user_model()
  count = lambda role: User.objects.filter(is_active=True, portal_profile__role=role).count()
  term = Term.objects.filter(is_current=True).first()
  students = [{"id": s.id, "name": display_name(s.user), "class_name": s.school_class.name}
              for s in Student.objects.filter(user__is_active=True)
              .select_related("user", "school_class").order_by("school_class__name", "user__first_name")]
  return JsonResponse({
      "stats": {"students": count("student"), "teachers": count("teacher"), "parents": count("parent"),
                "classes": SchoolClass.objects.count(), "subjects": Subject.objects.count()},
      "todo": {
          "no_teacher": ClassSubject.objects.filter(teacher__isnull=True).count(),
          "unlinked_students": Student.objects.filter(user__is_active=True, parent_links__isnull=True).count(),
      },
      "term": term.label() if term else None,
      "students": students,
  })