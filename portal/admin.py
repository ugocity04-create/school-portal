from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import (Announcement, Attendance, ClassSubject, Event, FeeInvoice, Homework, ParentLink,
                     Payment, Remark, SchoolClass, Score, Student, Subject, Submission, Term, TimetableEntry)

User = get_user_model()


class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    max_num = 1
    verbose_name = "Student details (only for students)"
    verbose_name_plural = "Student details (only for students: class and admission number)"


# Add our two boxes to the normal Django user page, whatever user admin you already have.
_current = admin.site._registry.get(User)
_base = type(_current) if _current is not None else admin.ModelAdmin
if _current is not None:
    admin.site.unregister(User)


@admin.register(User)
class SchoolUserAdmin(_base):
    inlines = list(getattr(_base, "inlines", [])) + [StudentInline]

    def get_inline_instances(self, request, obj=None):
        # The class box (students only) appears after the account is first saved.
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["__str__", "school_class", "admitted_on"]
    list_filter = ["school_class"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "admission_no"]


@admin.register(ParentLink)
class ParentLinkAdmin(admin.ModelAdmin):
    list_display = ["parent", "student"]
    search_fields = ["parent__username", "student__user__first_name", "student__user__last_name"]


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ["school_class", "subject", "teacher"]
    list_filter = ["school_class", "teacher"]


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ["__str__", "is_current"]


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ["student", "subject", "term", "ca1", "ca2", "exam"]
    list_filter = ["term", "subject", "student__school_class"]


@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    list_display = ["student", "teacher", "term", "created_at"]
    list_filter = ["term"]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["student", "date", "status"]
    list_filter = ["status", "date", "student__school_class"]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "audience", "pinned", "created_at"]
    list_filter = ["audience", "pinned"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "end_date"]


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ["school_class", "day", "period", "subject"]
    list_filter = ["school_class", "day"]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["homework", "student", "score", "late", "submitted_at"]


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ["title", "class_subject", "mode", "due_date"]
    list_filter = ["due_date"]


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(FeeInvoice)
class FeeInvoiceAdmin(admin.ModelAdmin):
    list_display = ["student", "term", "title", "amount"]
    list_filter = ["term", "student__school_class"]
    search_fields = ["student__user__first_name", "student__user__last_name"]
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["invoice", "amount", "paid_on", "method"]
    list_filter = ["method", "paid_on"]