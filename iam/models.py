from django.db import models
from django.contrib.auth.models import User

# User Profile
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_no = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    emergency_contact_no = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username


# Staff
class StaffProfile(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    position = models.CharField(max_length=50)
    staff_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.user_profile.user.username


# Student
class Student(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, unique=True)
    branch = models.CharField(max_length=100)
    year = models.IntegerField()

    def __str__(self):
        return f"{self.user_profile.user.username} ({self.roll_number})"
