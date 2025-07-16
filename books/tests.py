from django.test import TestCase
from django.contrib.auth.models import User
from iam.models import Student, UserProfile
from .models import Category, Author, Book, BookCopy, BorrowRecord
from datetime import date, timedelta

class BookModelTest(TestCase):

    def setUp(self):
        # User Setup
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.profile = UserProfile.objects.create(user=self.user, phone_no='1234567890', emergency_contact_no='9876543210')
        self.student = Student.objects.create(user_profile=self.profile, roll_number='101', branch='CS', year=2)

        # Category & Author
        self.category = Category.objects.create(name='Science', location='Aisle 1')
        self.author = Author.objects.create(name='Author One')

        # Book & BookCopy
        self.book = Book.objects.create(
            title='Test Book',
            isbn='1234567890123',
            category=self.category,
            description='A test book.',
            published_date='2020',
            recommended=True
        )
        self.book.authors.add(self.author)

        self.copy = BookCopy.objects.create(
            book=self.book,
            status='available',
            no_of_copies='C001'
        )

    def test_book_creation(self):
        self.assertEqual(self.book.title, 'Test Book')
        self.assertEqual(self.book.isbn, '1234567890123')
        self.assertTrue(self.book.recommended)

    def test_borrow_record(self):
        borrow = BorrowRecord.objects.create(
            student=self.student,
            book_copy=self.copy,
            borrow_date=date.today(),
            due_date=date.today() + timedelta(days=7)
        )
        self.assertEqual(borrow.book_copy.status, 'available')
        self.assertEqual(borrow.student.roll_number, '101')
