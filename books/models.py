from django.db import models
from datetime import date
from iam.models import Student, UserProfile
from subscription.models import StudentSubscription, SubscriptionPlan  


# 🔹 Author model
class Author(models.Model):
    name = models.CharField(max_length=100)  # लेखकाचे नाव

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
    title = models.CharField(max_length=200)  # पुस्तकाचं नाव
    authors = models.ManyToManyField(Author)  # लेखकांची यादी
    isbn = models.CharField(max_length=13, unique=True)  # Unique ISBN
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField()  # पुस्तकाची माहिती
    published_date = models.DateField()  # प्रकाशन तारीख
    recommended = models.BooleanField(default=False)  # शिफारसीत पुस्तक?
    allowed_in_plans = models.ManyToManyField(SubscriptionPlan, blank=True)  # कोणत्या योजना या पुस्तकाला परवानगी देतात

    def __str__(self):
        return self.title

    # ✅ नवीन METHOD - उपलब्ध copies count करते
    def available_copies_count(self):
        """
        ✅ या method ने पुस्तकाच्या उपलब्ध copies count होतात.
        म्हणजेच status = 'available' असलेल्या BookCopy objects ची count.
        """
        return self.bookcopy_set.filter(status='available').count()


# 🔹 Book Copies
class BookCopy(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE)  # पुस्तक संदर्भ
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')  # स्टेटस
    copy_id = models.CharField(max_length=30, unique=True, default='default_copy')  # ✅ Unique ID for each copy
    library_location = models.CharField(max_length=100, default='Main Branch')  # कोणत्या शाखेत आहे?

    def __str__(self):
        return f"{self.book.title} - {self.copy_id} - {self.status}"


# 🔹 Borrow Record
class BorrowRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)  # कोणत्या विद्यार्थ्याने घेतलं
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE)  # कोणती कॉपी घेतली
    borrow_date = models.DateField(auto_now_add=True)  # जेव्हा घेतलं
    due_date = models.DateField()  # परत करण्याची शेवटची तारीख
    return_date = models.DateField(null=True, blank=True)  # परत केलं का?

    def __str__(self):
        return f"{self.student.user_profile.user.username} - {self.book_copy.book.title}"

    def is_late(self):
        return self.return_date and self.return_date > self.due_date

    def get_fine_amount(self):
        """
        ✅ उशिर झाल्यास फाइन कसा लागेल हे calculate करतं.
        """
        if self.return_date and self.return_date > self.due_date:
            late_days = (self.return_date - self.due_date).days
            try:
                subscription = StudentSubscription.objects.filter(student=self.student).last()
                if subscription:
                    fine_rate = subscription.plan.fine_per_day
                    return late_days * fine_rate
            except StudentSubscription.DoesNotExist:
                pass
            return late_days * 10  # जर योजना नसेल, default ₹10 per day
        return 0

    def fine_rate(self):
        """
        प्रत्येक विद्यार्थ्याच्या subscription plan नुसार प्रति दिवस दंड परत करतो.
        """
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
    )  # एकच फाइन एका record ला
    amount = models.DecimalField(max_digits=6, decimal_places=2)  # रक्कम
    paid = models.BooleanField(default=False)  # भरले आहे का?

    def __str__(self):
        return f"{self.borrow_record} - ₹{self.amount}"
