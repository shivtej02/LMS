from django.contrib import admin
from .models import UserProfile, StaffProfile, Student

admin.site.register(UserProfile)
admin.site.register(StaffProfile)
admin.site.register(Student)
