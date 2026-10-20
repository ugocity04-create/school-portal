from django.urls import path

from . import views, views_extra as x

urlpatterns = [
    # sign in
    path("me/", views.me),
    path("me/photo/", x.my_photo),
    path("login/", views.login_view),
    path("logout/", views.logout_view),
    path("change-password/", views.change_password),
    path("terms/", views.terms),

    # results
    path("student/me/", views.my_student),
    path("parent/children/", views.my_children),
    path("students/<int:sid>/report/", views.student_report),
    path("students/<int:sid>/progress/", x.student_progress),
    path("students/<int:sid>/attendance/", x.student_attendance),
    path("students/<int:sid>/timetable/", x.student_timetable),
    path("students/<int:sid>/homework/", x.student_homework),
    path("students/<int:sid>/fees/", x.student_fees),
    path("payments/<int:pid>/", x.payment_receipt),

    # teachers
    path("teacher/assignments/", views.teacher_assignments),
    path("teacher/assignments/<int:cs_id>/scores/", views.teacher_scores),
    path("teacher/assignments/<int:cs_id>/analytics/", x.teacher_subject_analytics),
    path("teacher/assignments/<int:cs_id>/homework/", x.teacher_homework),
    path("teacher/homework/<int:hid>/delete/", x.teacher_homework_delete),
    path("students/<int:sid>/homework/<int:hid>/", x.student_homework_detail),
    path("students/<int:sid>/homework/<int:hid>/submit/", x.student_homework_submit),
    path("teacher/homework/<int:hid>/submissions/", x.teacher_submissions),
    path("teacher/homework/<int:hid>/grade/<int:sid>/", x.teacher_grade),
    path("teacher/classes/<int:class_id>/students/", views.teacher_class_students),
    path("teacher/classes/<int:class_id>/attendance/", x.teacher_attendance),
    path("teacher/students/<int:sid>/remarks/", views.teacher_remarks),
    path("teacher/remarks/<int:rid>/delete/", views.teacher_remark_delete),
    path("teacher/timetable/", x.teacher_timetable),

    # notices (everyone) and the admin side
    path("notices/", x.notices),
    path("admin/overview/", views.admin_overview),
    path("admin/analytics/", x.admin_analytics),
    path("admin/notices/", x.admin_notice_list),
    path("admin/notices/create/", x.admin_notice_create),
    path("admin/notices/<int:nid>/delete/", x.admin_notice_delete),
    path("admin/events/create/", x.admin_event_create),
    path("admin/events/<int:eid>/delete/", x.admin_event_delete),
    path("admin/fees/", x.admin_fees),
    path("admin/fees/payment/", x.admin_record_payment),
    path("admin/fees/generate/", x.admin_generate_invoices),
]