"""Who may see what. Everything goes through these few functions."""
from .models import ClassSubject, ParentLink, Profile, Student

def role_of(user):
  """The account's role. Accounts made before this app existed get one on first use."""
  if not user.is_authenticated:
    return None
  profile = getattr(user, "portal_profile", None)
  if profile is None:
    profile, _ = Profile.objects.get_or_create(
      user=user, defaults={"role": "admin" if user.is_superuser else "student"})
  if user.is_superuser:
    return "admin"
  return profile.role

def can_view_student(user, student):
  role = role_of(user)
  if role == "admin":
    return True
  if role == "student":
    return student.user_id == user.id
  if role == "parent":
    return ParentLink.objects.filter(parent=user, student=student).exists()
  return False

def teacher_teaches_student(user, student):
  return ClassSubject.objects.filter(school_class=student.school_class, teacher=user).exists()

def students_of_class(school_class):
  return (Student.objects.filter(school_class=school_class, user__is_active=True)
          .select_related("user").order_by("user__first_name", "user__last_name", "user__username"))