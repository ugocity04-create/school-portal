from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
  ROLE_CHOICES = (
    ("admin", "Administrator"),
    ("teacher", "Teacher"),
    ("student", "Student"),
    ("parent", "Parent"),
  )
  role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student")
  phone_number = models.CharField(max_length=15, blank=True, null=True)
  
  REQUIRED_FIELDS = ["email", "role"]
  
  def __str__(self):
    return f"{self.username} ({self.get_role_display()})"