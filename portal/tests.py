"""Run with:  python manage.py test portal

These load the demo school into a temporary test database and call every part of the API
as each kind of user. If something is broken, the failing test name says which part.
"""
import datetime
import json

from django.core.management import call_command
from django.test import TestCase

from .models import Attendance, Homework, Payment, Score, Student, Term

PASSWORD = "demo1234"


class PortalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", "--with-admin", verbosity=0)

    # ------------------------------------------------------------- helpers
    def sign_in(self, username):
        self.client.logout()
        self.assertTrue(self.client.login(username=username, password=PASSWORD), username)

    def get(self, path, status=200):
        r = self.client.get("/api" + path)
        self.assertEqual(r.status_code, status, "%s -> %s %s" % (path, r.status_code, r.content[:300]))
        return json.loads(r.content)

    def post(self, path, body=None, status=200):
        r = self.client.post("/api" + path, data=json.dumps(body or {}), content_type="application/json")
        self.assertEqual(r.status_code, status, "%s -> %s %s" % (path, r.status_code, r.content[:300]))
        return json.loads(r.content)

    def student(self, username):
        return Student.objects.get(user__username=username)

    # ------------------------------------------------------------- sign in
    def test_login_and_me(self):
        self.assertIsNone(self.get("/me/")["user"])
        data = self.post("/login/", {"username": "ngozi.eze", "password": PASSWORD})
        self.assertEqual(data["user"]["role"], "teacher")
        self.assertEqual(self.get("/me/")["user"]["username"], "ngozi.eze")

    def test_wrong_password_and_lockout(self):
        for _ in range(5):
            self.post("/login/", {"username": "ada.nwosu", "password": "nope"}, status=400)
        self.post("/login/", {"username": "ada.nwosu", "password": PASSWORD}, status=429)

    def test_roles_are_correct(self):
        for username, role in (("ada.nwosu", "student"), ("emeka.nwosu", "parent"),
                               ("ngozi.eze", "teacher"), ("school.admin", "admin")):
            self.sign_in(username)
            self.assertEqual(self.get("/me/")["user"]["role"], role, username)

    def test_signed_out_is_refused(self):
        self.get("/terms/", status=401)
        self.get("/notices/", status=401)

    # ------------------------------------------------------------- student
    def test_student_pages(self):
        self.sign_in("ada.nwosu")
        sid = self.get("/student/me/")["student_id"]
        report = self.get("/students/%d/report/" % sid)
        self.assertEqual(report["student"]["name"], "Ada Nwosu")
        self.assertEqual(len(report["rows"]), 8)
        progress = self.get("/students/%d/progress/" % sid)
        self.assertGreater(len(progress["points"]), 2)
        self.assertTrue(progress["subjects"])
        attendance = self.get("/students/%d/attendance/" % sid)
        self.assertGreater(attendance["total"], 50)
        timetable = self.get("/students/%d/timetable/" % sid)
        self.assertEqual(len(timetable["rows"]), 8)            # 7 periods + the break
        self.get("/students/%d/homework/" % sid)
        self.get("/students/%d/fees/" % sid, status=403)      # fees are for parents and the office
        notices = self.get("/notices/")
        titles = [a["title"] for a in notices["announcements"]]
        self.assertIn("Welcome to the new term", titles)
        self.assertNotIn("Fees reminder", titles)             # that one is for parents

    def test_student_cannot_see_others(self):
        self.sign_in("ada.nwosu")
        other = self.student("tobi.adeleke")
        self.get("/students/%d/report/" % other.id, status=403)
        self.get("/students/%d/progress/" % other.id, status=403)
        self.get("/students/%d/attendance/" % other.id, status=403)

    # ------------------------------------------------------------- parent
    def test_parent_pages_and_fees(self):
        self.sign_in("emeka.nwosu")
        kids = self.get("/parent/children/")["children"]
        self.assertEqual(len(kids), 2)
        child = self.student("ada.nwosu")
        fees = self.get("/students/%d/fees/" % child.id)
        self.assertEqual(len(fees["invoices"]), 3)
        paid_id = Payment.objects.filter(invoice__student=child).first().id
        receipt = self.get("/payments/%d/" % paid_id)
        self.assertTrue(receipt["receipt_no"].startswith("GA-"))
        stranger = self.student("tobi.adeleke")
        self.get("/students/%d/fees/" % stranger.id, status=403)
        self.get("/students/%d/progress/" % stranger.id, status=403)
        titles = [a["title"] for a in self.get("/notices/")["announcements"]]
        self.assertIn("Fees reminder", titles)

    # ------------------------------------------------------------- teacher
    def teacher_assignment(self):
        self.sign_in("ngozi.eze")
        first = self.get("/teacher/assignments/")["assignments"][0]
        self.assertEqual(first["subject"], "English Language")
        return first

    def test_teacher_scores(self):
        cs = self.teacher_assignment()
        data = self.get("/teacher/assignments/%d/scores/" % cs["id"])
        self.assertTrue(data["editable"])
        rows = data["rows"]
        scores = [{"student_id": r["student_id"], "ca1": "10", "ca2": "11", "exam": "40"} for r in rows]
        self.post("/teacher/assignments/%d/scores/" % cs["id"], {"term_id": data["term"]["id"], "scores": scores})
        scores[0]["ca1"] = "25"                               # out of 20
        bad = self.post("/teacher/assignments/%d/scores/" % cs["id"],
                        {"term_id": data["term"]["id"], "scores": scores}, status=400)
        self.assertIn(str(rows[0]["student_id"]), {str(k) for k in bad["problems"]})
        old = Term.objects.exclude(is_current=True).first()
        self.post("/teacher/assignments/%d/scores/" % cs["id"],
                  {"term_id": old.id, "scores": scores}, status=403)
        # another teacher's subject
        self.sign_in("tunde.balogun")
        self.get("/teacher/assignments/%d/scores/" % cs["id"], status=403)

    def test_teacher_analytics_attendance_homework(self):
        cs = self.teacher_assignment()
        analytics = self.get("/teacher/assignments/%d/analytics/" % cs["id"])
        self.assertTrue(analytics["trend"])
        self.assertEqual(len(analytics["spread"]), 9)

        class_id = cs["class_id"]
        day = datetime.date.today()
        while day.weekday() > 4:
            day -= datetime.timedelta(days=1)
        register = self.get("/teacher/classes/%d/attendance/?date=%s" % (class_id, day.isoformat()))
        marks = [{"student_id": r["student_id"], "status": "present"} for r in register["rows"]]
        marks[0]["status"] = "absent"
        saved = self.post("/teacher/classes/%d/attendance/" % class_id, {"date": day.isoformat(), "marks": marks})
        self.assertTrue(saved["saved"])
        self.assertEqual(Attendance.objects.get(student_id=marks[0]["student_id"], date=day).status, "absent")
        future = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        self.post("/teacher/classes/%d/attendance/" % class_id, {"date": future, "marks": marks}, status=400)

        due = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        made = self.post("/teacher/assignments/%d/homework/" % cs["id"], {"title": "Essay on my town", "due_date": due,
                                                                     "mode": "notebook", "instructions": "Write about your town."})
        hw = [h for h in made["homework"] if h["title"] == "Essay on my town"][0]
        self.assertEqual(hw["title"], "Essay on my town")
        self.post("/teacher/homework/%d/delete/" % hw["id"])
        self.assertFalse(Homework.objects.filter(pk=hw["id"]).exists())
        self.get("/teacher/timetable/")

    def test_online_homework_submit_and_grade(self):
        cs = self.teacher_assignment()
        due = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        made = self.post("/teacher/assignments/%d/homework/" % cs["id"],
                         {"title": "Online quiz", "due_date": due, "mode": "online",
                          "instructions": "Answer the three questions.", "max_score": 10})
        hw = [h for h in made["homework"] if h["title"] == "Online quiz"][0]
        pupil = Student.objects.filter(school_class_id=cs["class_id"]).select_related("user").first()
        self.sign_in(pupil.user.username)
        detail = self.get("/students/%d/homework/%d/" % (pupil.id, hw["id"]))
        self.assertTrue(detail["can_submit"])
        self.assertEqual(detail["status"], "todo")
        self.post("/students/%d/homework/%d/submit/" % (pupil.id, hw["id"]), {"answer": ""}, status=400)
        done = self.post("/students/%d/homework/%d/submit/" % (pupil.id, hw["id"]), {"answer": "My answers."})
        self.assertEqual(done["submission"]["answer"], "My answers.")
        self.sign_in("ngozi.eze")
        listing = self.get("/teacher/homework/%d/submissions/" % hw["id"])
        self.assertTrue(any(r["submission"] for r in listing["rows"]))
        self.post("/teacher/homework/%d/grade/%d/" % (hw["id"], pupil.id), {"score": 99}, status=400)
        graded = self.post("/teacher/homework/%d/grade/%d/" % (hw["id"], pupil.id), {"score": 8, "feedback": "Well done"})
        self.assertTrue(graded["submission"]["graded"])
        self.sign_in(pupil.user.username)
        self.post("/students/%d/homework/%d/submit/" % (pupil.id, hw["id"]), {"answer": "Change"}, status=400)

    def test_teacher_remarks(self):
        self.sign_in("ngozi.eze")
        ada = self.student("ada.nwosu")
        data = self.post("/teacher/students/%d/remarks/" % ada.id, {"body": "Excellent effort this term."})
        self.assertEqual(data["remarks"][0]["body"], "Excellent effort this term.")
        self.sign_in("ada.nwosu")
        report = self.get("/students/%d/report/" % ada.id)
        self.assertIn("Excellent effort this term.", [m["body"] for m in report["remarks"]])

    # ------------------------------------------------------------- admin
    def test_admin_dashboard(self):
        self.sign_in("school.admin")
        self.get("/admin/overview/")
        data = self.get("/admin/analytics/")
        self.assertGreater(len(data["trend"]), 5)
        self.assertTrue(data["headline"])
        self.assertTrue(data["attendance"])
        self.assertTrue(data["fees"])
        pupils = [p["pupils"] for p in data["trend"]]
        self.assertEqual(pupils, sorted(pupils))              # the school only grows in the demo
        self.assertGreater(pupils[-1], pupils[0])

    def test_admin_notices_and_events(self):
        self.sign_in("school.admin")
        self.post("/admin/notices/create/", {"title": "Open day", "body": "Come and see our school.", "audience": "all"})
        self.post("/admin/notices/create/", {"title": "x", "body": "y"}, status=400)
        listed = self.get("/admin/notices/")["announcements"]
        target = next(a for a in listed if a["title"] == "Open day")
        self.post("/admin/notices/%d/delete/" % target["id"])
        day = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
        self.post("/admin/events/create/", {"title": "Quiz day", "date": day})
        self.sign_in("ada.nwosu")
        self.post("/admin/notices/create/", {"title": "Hack", "body": "no"}, status=403)

    def test_admin_fees(self):
        self.sign_in("school.admin")
        data = self.get("/admin/fees/")
        self.assertGreater(data["totals"]["billed"], 0)
        target = data["outstanding"][0]
        self.post("/admin/fees/payment/", {"invoice_id": target["invoice_id"], "amount": target["balance"] + 1,
                                           "method": "cash"}, status=400)
        done = self.post("/admin/fees/payment/", {"invoice_id": target["invoice_id"], "amount": 5000,
                                                  "method": "cash", "reference": "RCPT1"})
        self.assertTrue(Payment.objects.filter(pk=done["payment_id"]).exists())
        made = self.post("/admin/fees/generate/", {"title": "Sports levy", "amount": "5000"})
        self.assertEqual(made["created"], Student.objects.count())
        again = self.post("/admin/fees/generate/", {"title": "Sports levy", "amount": "5000"})
        self.assertEqual(again["created"], 0)                 # never bills twice

    # ------------------------------------------------------------- data sanity
    def test_demo_data_shape(self):
        self.assertEqual(Student.objects.count(), 20)
        self.assertGreater(Score.objects.count(), 500)