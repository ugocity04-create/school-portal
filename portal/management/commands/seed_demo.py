"""Fills the database with an invented demo school (Greenfield Academy).

    python manage.py seed_demo            first time
    python manage.py seed_demo --reset    wipe the demo data and load it again
    python manage.py seed_demo --with-admin   also make a demo admin (school.admin)

Every name here is invented. Never put real pupils into a demo.
All demo passwords are: demo1234
"""
import datetime
import random

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.grading import MAX_CA1, MAX_CA2, MAX_EXAM
from portal.models import (Announcement, Attendance, ClassSubject, Event, FeeInvoice, Homework,
                           ParentLink, Payment, Profile, Remark, SchoolClass, Score, Student, Subject,
                           Term, TimetableEntry, PERIODS)
from portal.analytics import term_end

User = get_user_model()

DEMO_PASSWORD = "demo1234"

SUBJECTS = ["English Language", "Mathematics", "Basic Science", "Basic Technology",
            "Social Studies", "Civic Education", "Computer Studies", "Business Studies"]

CLASSES = ["JSS 2A", "JSS 2B", "JSS 3A"]

# username, full name, subjects they teach (in every class)
TEACHERS = [
    ("ngozi.eze", "Mrs. Ngozi Eze", ["English Language"]),
    ("tunde.balogun", "Mr. Tunde Balogun", ["Mathematics"]),
    ("amina.yusuf", "Mrs. Amina Yusuf", ["Basic Science"]),
    ("chidi.okafor", "Mr. Chidi Okafor", ["Computer Studies", "Basic Technology"]),
    ("funke.adeyemi", "Mrs. Funke Adeyemi", ["Social Studies", "Civic Education"]),
    ("ibrahim.musa", "Mr. Ibrahim Musa", ["Business Studies"]),
]

# class -> students (username, full name, admission number)
STUDENTS = {
    "JSS 2A": [
        ("ada.nwosu", "Ada Nwosu", "GFA/25/011"), ("tobi.adeleke", "Tobi Adeleke", "GFA/25/012"),
        ("zainab.bello", "Zainab Bello", "GFA/25/013"), ("chinedu.okoro", "Chinedu Okoro", "GFA/25/014"),
        ("ifeoma.obi", "Ifeoma Obi", "GFA/25/015"), ("samuel.ojo", "Samuel Ojo", "GFA/25/016"),
        ("halima.garba", "Halima Garba", "GFA/25/017"), ("david.eze", "David Eze", "GFA/25/018"),
    ],
    "JSS 2B": [
        ("blessing.udoh", "Blessing Udoh", "GFA/25/021"), ("kemi.alabi", "Kemi Alabi", "GFA/25/022"),
        ("musa.ibrahim", "Musa Ibrahim", "GFA/25/023"), ("grace.okonkwo", "Grace Okonkwo", "GFA/25/024"),
        ("tolu.bakare", "Tolu Bakare", "GFA/25/025"), ("yusuf.lawal", "Yusuf Lawal", "GFA/25/026"),
    ],
    "JSS 3A": [
        ("kelechi.nwosu", "Kelechi Nwosu", "GFA/24/031"), ("funmi.adebayo", "Funmi Adebayo", "GFA/24/032"),
        ("hassan.abubakar", "Hassan Abubakar", "GFA/24/033"), ("precious.etim", "Precious Etim", "GFA/24/034"),
        ("segun.ajayi", "Segun Ajayi", "GFA/24/035"), ("amaka.chukwu", "Amaka Chukwu", "GFA/24/036"),
    ],
}

# parent username, full name, children's usernames
PARENTS = [
    ("emeka.nwosu", "Mr. Emeka Nwosu", ["ada.nwosu", "kelechi.nwosu"]),
    ("bola.adeleke", "Mrs. Bola Adeleke", ["tobi.adeleke"]),
    ("sani.bello", "Mr. Sani Bello", ["zainab.bello"]),
    ("njideka.okoro", "Mrs. Njideka Okoro", ["chinedu.okoro"]),
    ("peter.obi", "Mr. Peter Obi-Ugo", ["ifeoma.obi"]),
    ("aisha.garba", "Mrs. Aisha Garba", ["halima.garba"]),
    ("grace.eze", "Mrs. Grace Eze", ["david.eze"]),
    ("effiong.udoh", "Mr. Effiong Udoh", ["blessing.udoh"]),
    ("sade.alabi", "Mrs. Sade Alabi", ["kemi.alabi"]),
    ("ibrahim.senior", "Alhaji Ibrahim Sule", ["musa.ibrahim"]),
    ("dayo.bakare", "Mr. Dayo Bakare", ["tolu.bakare"]),
    ("fatima.lawal", "Mrs. Fatima Lawal", ["yusuf.lawal"]),
    ("bayo.adebayo", "Mr. Bayo Adebayo", ["funmi.adebayo"]),
    ("zara.abubakar", "Mrs. Zara Abubakar", ["hassan.abubakar"]),
    ("etim.sr", "Mr. Ime Etim", ["precious.etim"]),
    ("kayode.ajayi", "Mr. Kayode Ajayi", ["segun.ajayi"]),
    ("ngozi.chukwu", "Mrs. Ngozi Chukwu", ["amaka.chukwu"]),
]
# Samuel Ojo and Grace Okonkwo have no parent linked yet, on purpose,
# so the admin page can show the "unlinked students" hint.

REMARKS_HIGH = [
    "Consistently diligent and curious. Takes part well in class and helps classmates.",
    "Excellent work this term. Reading beyond the textbook will keep the challenge going.",
    "A pleasure to teach. Neat, punctual and always prepared.",
]
REMARKS_MID = [
    "Making steady progress. Regular practice with past questions will lift the result.",
    "Good attitude in class. Should ask for help earlier when a topic is unclear.",
    "Capable of more. Check homework carefully before handing it in.",
]
REMARKS_LOW = [
    "Needs to complete homework regularly. A short daily study routine will help a lot.",
    "Has potential but loses focus in class. We would like to meet and agree a plan.",
    "Struggling with the basics of this term's topics. Extra practice at home is advised.",
]



def _score(rng, ability, affinity, maximum):
    value = maximum * (ability + affinity) + rng.gauss(0, 0.07 * maximum)
    value = max(0.0, min(float(maximum), value))
    return round(value * 2) / 2          # halves, like a marked paper


TERMS = [("2023/2024", 1), ("2023/2024", 2), ("2023/2024", 3),
         ("2024/2025", 1), ("2024/2025", 2), ("2024/2025", 3),
         ("2025/2026", 1), ("2025/2026", 2), ("2025/2026", 3),
         ("2026/2027", 1)]
CURRENT = ("2026/2027", 1)

FEES = {"JSS 2A": 85000, "JSS 2B": 85000, "JSS 3A": 95000}


def _weekdays_back(count):
    days, d = [], datetime.date.today()
    while len(days) < count:
        if d.weekday() < 5:
            days.append(d)
        d -= datetime.timedelta(days=1)
    return days


class Command(BaseCommand):
    help = "Load the invented demo school."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete the demo data first.")
        parser.add_argument("--with-admin", action="store_true", help="Also create a demo admin.")

    def handle(self, *args, **opts):
        demo_usernames = ["school.admin"] + [t[0] for t in TEACHERS] + \
            [s[0] for people in STUDENTS.values() for s in people] + [p[0] for p in PARENTS]
        if User.objects.filter(username="ada.nwosu").exists():
            if not opts["reset"]:
                raise CommandError("Demo data is already loaded. Use --reset to load it again.")
        with transaction.atomic():
            if opts["reset"]:
                for model in (Payment, FeeInvoice, Homework, TimetableEntry, Attendance, Announcement, Event,
                              Remark, Score, ParentLink, ClassSubject, Student, Term, Subject, SchoolClass):
                    model.objects.all().delete()
                User.objects.filter(username__in=demo_usernames).delete()
            self._load(opts["with_admin"])
        self.stdout.write(self.style.SUCCESS("Demo school loaded. Password for every demo account: %s" % DEMO_PASSWORD))

    def _load(self, with_admin):
        rng = random.Random(2026)
        hashed = make_password(DEMO_PASSWORD)       # hash once, reuse for every demo account

        def add_user(username, full_name, role, **extra):
            first, _, last = full_name.rpartition(" ")
            if any(f.name == "role" for f in User._meta.get_fields()):
                extra["role"] = role                 # your user model has its own role field
            user = User(username=username, first_name=first, last_name=last, password=hashed, **extra)
            user.save()
            Profile.objects.update_or_create(user=user, defaults={"role": role})
            return user

        admin_user = None
        if with_admin:
            admin_user = add_user("school.admin", "School Administrator", "admin", is_staff=True, is_superuser=True)

        subjects = {n: Subject.objects.create(name=n) for n in SUBJECTS}
        classes = {n: SchoolClass.objects.create(name=n) for n in CLASSES}

        teacher_of, teachers = {}, {}
        for username, name, subs in TEACHERS:
            teacher = add_user(username, name, "teacher")
            teachers[username] = teacher
            for s in subs:
                teacher_of[s] = teacher
        class_subjects = {}
        for cname, klass in classes.items():
            for sname, subject in subjects.items():
                class_subjects[(cname, sname)] = ClassSubject.objects.create(
                    school_class=klass, subject=subject, teacher=teacher_of[sname])

        # admission dates make the school grow over the years: 6, 11, 16, then 20 pupils
        join_dates = [datetime.date(2023, 9, 18)] * 6 + [datetime.date(2024, 9, 16)] * 5 + \
                     [datetime.date(2025, 9, 15)] * 5 + [datetime.date(2026, 9, 14)] * 4
        people = [(c, p) for c, plist in STUDENTS.items() for p in plist]
        # the oldest pupils (JSS 3A) joined first
        people.sort(key=lambda cp: 0 if cp[0] == "JSS 3A" else 1)

        students, ability, class_of = {}, {}, {}
        for (cname, (username, name, adm)), joined in zip(people, join_dates):
            user = add_user(username, name, "student")
            st = Student.objects.create(user=user, school_class=classes[cname], admission_no=adm,
                                        admitted_on=joined)
            students[username] = st
            class_of[st.id] = cname
            ability[st.id] = rng.uniform(0.45, 0.92)

        parents = {}
        for username, name, kids in PARENTS:
            parent = add_user(username, name, "parent")
            parents[username] = parent
            for kid in kids:
                ParentLink.objects.create(parent=parent, student=students[kid])

        term_objs = {}
        for session_name, no in TERMS:
            term_objs[(session_name, no)] = Term.objects.create(
                session=session_name, term_no=no, is_current=(session_name, no) == CURRENT)
        current_term = term_objs[CURRENT]

        pending_exam_subjects = {"Computer Studies", "Business Studies"}   # exams not marked yet this term
        # the school improves over the years (with a small wobble), so the growth chart has a story
        drift = {key: -0.13 + 0.017 * i + rng.uniform(-0.015, 0.015) for i, key in enumerate(TERMS)}

        scores = []
        for st in students.values():
            base = ability[st.id]
            affinity = {s: rng.uniform(-0.12, 0.12) for s in SUBJECTS}
            for key, term in term_objs.items():
                if term_end(term) < st.admitted_on:
                    continue                          # the pupil had not joined yet
                for sname, subject in subjects.items():
                    level = base + drift[key]
                    ca1 = _score(rng, level, affinity[sname], MAX_CA1)
                    ca2 = _score(rng, level, affinity[sname], MAX_CA2)
                    exam = _score(rng, level, affinity[sname], MAX_EXAM)
                    if term == current_term and sname in pending_exam_subjects:
                        exam = None
                    scores.append(Score(student=st, subject=subject, term=term, ca1=ca1, ca2=ca2,
                                        exam=exam, updated_by=teacher_of[sname]))
        Score.objects.bulk_create(scores)

        # a few teacher remarks, matched to how the pupil is doing
        for st in students.values():
            if rng.random() < 0.35:
                continue
            base = ability[st.id]
            pool = REMARKS_HIGH if base > 0.72 else REMARKS_MID if base > 0.55 else REMARKS_LOW
            sname = rng.choice(SUBJECTS)
            general = rng.random() < 0.4
            for term in (current_term, term_objs[("2025/2026", 3)]):
                Remark.objects.create(student=st, term=term, teacher=teacher_of[sname],
                                      subject=None if general else subjects[sname], body=rng.choice(pool))

        # attendance for roughly the last six months of school days
        records = []
        for st in students.values():
            rate = 0.86 + 0.12 * ability[st.id]
            for day in _weekdays_back(125):
                if day < st.admitted_on:
                    continue
                roll = rng.random()
                status = "present" if roll < rate else ("late" if roll < rate + 0.04 else "absent")
                records.append(Attendance(student=st, date=day, status=status))
        Attendance.objects.bulk_create(records)

        # timetable: every class gets a full week
        names = list(SUBJECTS)
        for ci, (cname, klass) in enumerate(classes.items()):
            for day in range(5):
                for period, _, _ in PERIODS:
                    pick = names[(day * 3 + period * 2 + ci * 3) % len(names)]
                    TimetableEntry.objects.create(school_class=klass, day=day, period=period,
                                                  subject=subjects[pick])

        # homework: a couple of items per class subject, some due soon, some recently past
        today = datetime.date.today()
        topics = ["Chapter exercise", "Practice questions", "Mini project", "Revision worksheet"]
        for (cname, sname), cs in class_subjects.items():
            for offset, label in ((rng.randint(1, 4), "Practice questions"), (rng.randint(6, 12), "Mini project"),
                                  (-rng.randint(2, 6), "Revision worksheet")):
                online = label == "Mini project"
                text = ("Write a short answer (5 to 8 sentences) to each question below and hand it in here.\n"
                        "1. Explain the main idea you learned in %s this week.\n"
                        "2. Give one example from your own life.\n"
                        "3. Write one question you still want to ask your teacher." % sname) if online else (
                        "Do exercises 1 to 5 on the topic we just finished in %s. Write your working neatly "
                        "in your notebook and bring it on the due date." % sname)
                Homework.objects.create(
                    class_subject=cs, title="%s: %s" % (sname, label), due_date=today + datetime.timedelta(days=offset),
                    mode="online" if online else "notebook", max_score=10, instructions=text,
                    description=" ".join(text.split())[:140])

        # notice board and events
        office = admin_user
        Announcement.objects.create(title="Welcome to the new term", pinned=True, audience="all", created_by=office,
            body="Classes are running as normal. Please check the timetable on your child's page and report any mistakes to the school office.")
        Announcement.objects.create(title="Mid-term break", audience="all", created_by=office,
            body="School closes for mid-term break at 1:10 pm on the Friday of week 6 and resumes the following Monday.")
        Announcement.objects.create(title="Fees reminder", audience="parents", created_by=office,
            body="Please clear any outstanding balance before exams begin. Payments can be made at the bursary or by transfer. Quote your child's admission number.")
        Announcement.objects.create(title="Scores deadline", audience="teachers", created_by=office,
            body="All first and second test scores must be entered before the end of week 8. Exam scores follow after the exam period.")
        Announcement.objects.create(title="Inter-house sports training", audience="students", created_by=office,
            body="Training for the inter-house sports starts this week. Come in your house colours after school on Wednesday and Friday.")
        Event.objects.create(title="PTA meeting", date=today + datetime.timedelta(days=9), description="Hall, 10:00 am. Parents are encouraged to attend.")
        Event.objects.create(title="Inter-house sports", date=today + datetime.timedelta(days=21), description="School field, all day.")
        Event.objects.create(title="Mid-term break", date=today + datetime.timedelta(days=30), end_date=today + datetime.timedelta(days=32))
        Event.objects.create(title="Examinations begin", date=today + datetime.timedelta(days=55), end_date=today + datetime.timedelta(days=63))
        Event.objects.create(title="Third term resumes (next session)", date=today + datetime.timedelta(days=120))

        # fees: last term fully paid, this term a mix of paid, part paid and unpaid
        last_term = term_objs[("2025/2026", 3)]
        methods = ["transfer", "transfer", "cash", "pos"]
        for st in students.values():
            fee = FEES[class_of[st.id]]
            old = FeeInvoice.objects.create(student=st, term=last_term, title="School fees", amount=fee)
            Payment.objects.create(invoice=old, amount=fee, paid_on=datetime.date(2026, 4, 28), method=rng.choice(methods),
                                   reference="TRF%08d" % rng.randint(0, 99999999), recorded_by=office)
            new = FeeInvoice.objects.create(student=st, term=current_term, title="School fees", amount=fee)
            FeeInvoice.objects.create(student=st, term=current_term, title="Textbooks and levy", amount=15000)
            roll = rng.random()
            if roll < 0.45:
                paid = fee
            elif roll < 0.75:
                paid = int(fee * rng.choice([0.4, 0.5, 0.6]) / 1000) * 1000
            else:
                paid = 0
            if paid:
                Payment.objects.create(invoice=new, amount=paid, paid_on=today - datetime.timedelta(days=rng.randint(3, 25)),
                                       method=rng.choice(methods), reference="TRF%08d" % rng.randint(0, 99999999),
                                       recorded_by=office)