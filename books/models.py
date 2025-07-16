from django.db import models
from datetime import date
from iam.models import Student, UserProfile
from subscription.models import StudentSubscription, SubscriptionPlan  


# 🔹 Author model
class Author(models.Model):
    name = models.CharField(max_length=100)  # Author name

    def __str__(self):
        return self.name


# 🔹 Book Category
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Category name
    location = models.CharField(max_length=100)  # Library rack/section

    def __str__(self):
        return self.name


# 🔹 Book Info
class Book(models.Model):
    title = models.CharField(max_length=200)  # Book name
    authors = models.ManyToManyField(Author)  # Authoe list
    isbn = models.CharField(max_length=13, unique=True)  # Unique ISBN
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField()  # Book info.
    published_date = models.DateField()  # Publish date
    recommended = models.BooleanField(default=False)  # Recommended Books
    allowed_in_plans = models.ManyToManyField(SubscriptionPlan, blank=True)  #Subscription plan allow to books

    def __str__(self):
        return self.title

    def available_copies_count(self):
        return self.bookcopy_set.filter(status='available').count()


# 🔹 Book Copies
class BookCopy(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE) 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')  
    copy_id = models.CharField(max_length=30, unique=True, default='default_copy')  # ✅ Unique ID for each copy
    library_location = models.CharField(max_length=100, default='Main Branch') 

    def __str__(self):
        return f"{self.book.title} - {self.copy_id} - {self.status}"


# 🔹 Borrow Record
class BorrowRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)  # Which student can borrow 
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE)  # Which copies borrow
    borrow_date = models.DateField(auto_now_add=True)  
    due_date = models.DateField() 
    return_date = models.DateField(null=True, blank=True) 

    def __str__(self):
        return f"{self.student.user_profile.user.username} - {self.book_copy.book.title}"

    def is_late(self):
        return self.return_date and self.return_date > self.due_date

    def get_fine_amount(self):

        if self.return_date and self.return_date > self.due_date:
            late_days = (self.return_date - self.due_date).days
            try:
                subscription = StudentSubscription.objects.filter(student=self.student).last()
                if subscription:
                    fine_rate = subscription.plan.fine_per_day
                    return late_days * fine_rate
            except StudentSubscription.DoesNotExist:
                pass
            return late_days * 10  
        return 0

    def fine_rate(self):

        try:
            subscription = StudentSubscription.objects.filter(student=self.student).last()
            if subscription:
                return subscription.plan.fine_per_day
        except StudentSubscription.DoesNotExist:
            return 10
        return 10


# 🔹 Fine Model
class Fine(models.Model):
    borrow_record = models.OneToOneField(
        BorrowRecord,
        on_delete=models.CASCADE,
        related_name='book_fine'
    )  
    amount = models.DecimalField(max_digits=6, decimal_places=2)  
    paid = models.BooleanField(default=False) 

    def __str__(self):
        return f"{self.borrow_record} - ₹{self.amount}"
