from django.db import models
from iam.models import Student, StaffProfile
from datetime import timedelta


# 🔹 Subscription Plan
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)  # Plan name (e.g., Basic, Premium)
    max_books = models.PositiveIntegerField()  # how many books can be borrowed
    duration_days = models.PositiveIntegerField()  # Validity in days
    price = models.DecimalField(max_digits=6, decimal_places=2)  # ₹ price
    fine_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Daily fine

    def __str__(self):
        return self.name


# 🔹 Student's Chosen Subscription
class StudentSubscription(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)

    @property
    def end_date(self):
        return self.start_date + timedelta(days=self.plan.duration_days)

    def __str__(self):
        return f"{self.student.user_profile.user.username} subscribed to {self.plan.name}"

    class Meta:
        unique_together = ('student', 'plan')  # Optional: prevent duplicate subscriptions


# 🔹 Fine for Borrowed Books (from books app)
class Fine(models.Model):
    borrow_record = models.OneToOneField(
        'books.BorrowRecord',
        on_delete=models.CASCADE,
        related_name='subscription_fine'
    )
    amount = models.DecimalField(max_digits=6, decimal_places=2)  # ₹ amount of fine
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.borrow_record.student.user_profile.user.username} - ₹{self.amount}"


# 🔹 Bulk Book Uploads (by Staff only)
class BulkUpload(models.Model):
    uploaded_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)
    upload_file = models.FileField(upload_to='bulk_uploads/')  # File path
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Upload by {self.uploaded_by.user_profile.user.username} on {self.uploaded_at}"
