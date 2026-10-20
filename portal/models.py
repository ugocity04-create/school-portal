import datetime

from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Profile(models.Model):
    """What kind of person this account is. Created automatically for every user."""
    ROLES = [("student", "Student"), ("parent", "Parent"),
             ("teacher", "Teacher"), ("admin", "Admin")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="portal_profile")
    role = models.CharField(max_length=10, choices=ROLES, default="student")
    photo = models.FileField(upload_to="photos/", blank=True)

    def __str__(self):
        return "%s (%s)" % (self.user, self.role)


class SchoolClass(models.Model):
    name = models.CharField(max_length=30, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "classes"

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name="students")
    admission_no = models.CharField(max_length=30, unique=True)
    admitted_on = models.DateField(default=datetime.date.today,
                                   help_text="Used for the school growth chart.")

    def __str__(self):
        return "%s (%s)" % (self.user.get_full_name() or self.user.get_username(), self.admission_no)


class ParentLink(models.Model):
    """Which parent can see which child."""
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="children_links")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="parent_links")

    class Meta:
        unique_together = [("parent", "student")]

    def __str__(self):
        return "%s -> %s" % (self.parent, self.student)


class ClassSubject(models.Model):
    """A subject taught in a class, by one teacher."""
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="class_subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="class_subjects")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="teaching", limit_choices_to={"portal_profile__role": "teacher"})

    class Meta:
        unique_together = [("school_class", "subject")]
        ordering = ["school_class__name", "subject__name"]

    def __str__(self):
        return "%s: %s" % (self.school_class, self.subject)


class Term(models.Model):
    session = models.CharField(max_length=9, help_text="For example 2026/2027")
    term_no = models.PositiveSmallIntegerField(choices=[(1, "First"), (2, "Second"), (3, "Third")])
    is_current = models.BooleanField(default=False,
                                     help_text="Teachers can only change scores in the current term.")

    class Meta:
        unique_together = [("session", "term_no")]
        ordering = ["-session", "-term_no"]

    def label(self):
        return "%s Term, %s session" % (self.get_term_no_display(), self.session)

    def __str__(self):
        return self.label()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:                      # only one current term at a time
            Term.objects.exclude(pk=self.pk).filter(is_current=True).update(is_current=False)


class Score(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="scores")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="scores")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="scores")
    ca1 = models.FloatField(null=True, blank=True)
    ca2 = models.FloatField(null=True, blank=True)
    exam = models.FloatField(null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("student", "subject", "term")]

    def __str__(self):
        return "%s %s %s" % (self.student, self.subject, self.term)


class Remark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="remarks")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="remarks")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="remarks_written")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    body = models.TextField(max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return "Remark on %s" % self.student


# ---------------------------------------------------------------- attendance

class Attendance(models.Model):
    STATUS = [("present", "Present"), ("absent", "Absent"), ("late", "Late")]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        unique_together = [("student", "date")]
        ordering = ["-date"]

    def __str__(self):
        return "%s %s %s" % (self.student, self.date, self.status)


# ---------------------------------------------------------------- notices and events

class Announcement(models.Model):
    AUDIENCE = [("all", "Everyone"), ("students", "Students"),
                ("parents", "Parents"), ("teachers", "Teachers")]
    title = models.CharField(max_length=120)
    body = models.TextField(max_length=1000)
    audience = models.CharField(max_length=10, choices=AUDIENCE, default="all")
    pinned = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pinned", "-created_at"]

    def __str__(self):
        return self.title


class Event(models.Model):
    title = models.CharField(max_length=120)
    date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return "%s (%s)" % (self.title, self.date)


# ---------------------------------------------------------------- timetable and homework

# (period number, start, end). A break sits between periods 4 and 5.
PERIODS = [(1, "08:00", "08:40"), (2, "08:40", "09:20"), (3, "09:20", "10:00"), (4, "10:00", "10:40"),
           (5, "11:10", "11:50"), (6, "11:50", "12:30"), (7, "12:30", "13:10")]
BREAK = ("10:40", "11:10")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]


class TimetableEntry(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="timetable")
    day = models.PositiveSmallIntegerField(choices=list(enumerate(DAYS)))
    period = models.PositiveSmallIntegerField(choices=[(p[0], "Period %d" % p[0]) for p in PERIODS])
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="timetable_entries")

    class Meta:
        unique_together = [("school_class", "day", "period")]
        ordering = ["school_class__name", "day", "period"]
        verbose_name_plural = "timetable entries"

    def __str__(self):
        return "%s %s P%d %s" % (self.school_class, DAYS[self.day], self.period, self.subject)


class Homework(models.Model):
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name="homework")
    title = models.CharField(max_length=120)
    description = models.TextField(max_length=600, blank=True)       # short line shown in lists
    instructions = models.TextField(max_length=4000, blank=True)     # the full task pupils open and read
    MODES = [("notebook", "In the notebook"), ("online", "Online in the portal")]
    mode = models.CharField(max_length=10, choices=MODES, default="notebook")
    max_score = models.PositiveSmallIntegerField(default=10)          # used for online work
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "id"]
        verbose_name_plural = "homework"

    def __str__(self):
        return "%s: %s" % (self.class_subject, self.title)


class Submission(models.Model):
    """A pupil's answer to online homework, and the teacher's grade."""
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="submissions")
    answer = models.TextField(max_length=8000)
    submitted_at = models.DateTimeField(auto_now=True)
    late = models.BooleanField(default=False)
    score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    feedback = models.TextField(max_length=1000, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("homework", "student")]

    def __str__(self):
        return "%s - %s" % (self.student, self.homework)


# ---------------------------------------------------------------- fees (records only, no real money moves here)

class FeeInvoice(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="invoices")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="invoices")
    title = models.CharField(max_length=80, default="School fees")
    amount = models.PositiveIntegerField(help_text="Naira")

    class Meta:
        unique_together = [("student", "term", "title")]
        ordering = ["-term__session", "-term__term_no", "title"]

    def __str__(self):
        return "%s: %s (%s)" % (self.student, self.title, self.term)

    def paid(self):
        return sum(p.amount for p in self.payments.all())

    def balance(self):
        return self.amount - self.paid()


class Payment(models.Model):
    METHODS = [("cash", "Cash"), ("transfer", "Bank transfer"), ("pos", "POS"), ("online", "Online")]
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.PositiveIntegerField(help_text="Naira")
    paid_on = models.DateField(default=datetime.date.today)
    method = models.CharField(max_length=10, choices=METHODS, default="transfer")
    reference = models.CharField(max_length=40, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        ordering = ["-paid_on", "-id"]

    def __str__(self):
        return "Payment %s of %s" % (self.pk, self.amount)