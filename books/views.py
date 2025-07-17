from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from django.db.models import Q
from datetime import timedelta, date
import csv
import io

from .models import Book, BookCopy, BorrowRecord, Fine  # ✅ Models used for logic
from iam.models import Student, UserProfile  # ✅ User identity
from subscription.models import StudentSubscription  # ✅ Subscription data
from django.contrib.auth.models import User

class BookCopiesView(LoginRequiredMixin, View):
    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        copies = BookCopy.objects.filter(book=book)
        return render(request, 'books/book_copies.html', {
            'book': book,
            'copies': copies
        })


class BookDetailView(LoginRequiredMixin, View):
    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        copies = BookCopy.objects.filter(book=book)
        available_copies = copies.filter(status='available').count()

        return render(request, 'books/book_detail.html', {
            'book': book,
            'copies': copies,
            'available_copies': available_copies
        })


class BookListView(LoginRequiredMixin, View):
    def get(self, request):
        books = Book.objects.all()
        book_data = []

        for book in books:
            available_copies = book.available_copies_count()
            copies = BookCopy.objects.filter(book=book)
            is_allowed = available_copies > 0
            can_borrow = copies.filter(status='available').exists()

            book_data.append({
                'book': book,
                'available_copies': available_copies,
                'copies': copies,
                'is_allowed': is_allowed,
                'can_borrow': can_borrow,
            })

        return render(request, 'books/book_list.html', {'book_data': book_data})


class BookSearchView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '')
        books = Book.objects.all()

        if query:
            books = books.filter(
                Q(title__icontains=query) |
                Q(authors__name__icontains=query) |
                Q(isbn__icontains=query) |
                Q(category__name__icontains=query)
            ).distinct()

        book_data = []
        for book in books:
            available_copies = book.available_copies_count()
            copies = BookCopy.objects.filter(book=book)
            is_allowed = available_copies > 0
            can_borrow = copies.filter(status='available').exists()

            book_data.append({
                'book': book,
                'available_copies': available_copies,
                'copies': copies,
                'is_allowed': is_allowed,
                'can_borrow': can_borrow,
            })

        return render(request, 'books/search_results.html', {
            'books': books,
            'query': query,
            'book_data': book_data
        })


class BorrowBookView(LoginRequiredMixin, View):
    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        available_copy = BookCopy.objects.filter(book=book, status='available').first()

        if not available_copy:
            return render(request, 'books/error.html', {'message': '❌ No available copy found.'})

        user_profile = get_object_or_404(UserProfile, user=request.user)
        student = get_object_or_404(Student, user_profile=user_profile)

        subscription = StudentSubscription.objects.filter(student=student).last()
        if not subscription:
            return render(request, 'books/error.html', {'message': '❌ You must subscribe to a plan before borrowing.'})

        expiry_date = subscription.start_date + timedelta(days=subscription.plan.duration_days)
        if date.today() > expiry_date:
            return render(request, 'books/error.html', {'message': '❌ Your subscription has expired.'})

        # 🔄 Updated: Check for unpaid fines
        unpaid_fines = Fine.objects.filter(borrow_record__student=student, paid=False)
        if unpaid_fines.exists():
            return render(request, 'books/error.html', {'message': '❌ You have unpaid fines. Please clear them before borrowing.'})

        # 🔄 Updated: Check if student has reached book limit
        active_borrows = BorrowRecord.objects.filter(student=student, return_date__isnull=True).count()
        if active_borrows >= subscription.plan.max_books:
            return render(request, 'books/error.html', {
                'message': f'❌ You have reached your limit of {subscription.plan.max_books} books.'
            })

        # ✅ Borrowing is allowed, create record
        BorrowRecord.objects.create(
            student=student,
            book_copy=available_copy,
            borrow_date=date.today(),
            due_date=date.today() + timedelta(days=7),
        )

# ✅ Feature: Send Email Reminder 1 day before due date
def send_due_soon_reminders():
    # उद्याचा दिवस
    tomorrow = date.today() + timedelta(days=1)

    # ज्यांचं due_date उद्या आहे आणि अजून return केलेलं नाही
    due_soon = BorrowRecord.objects.filter(due_date=tomorrow, return_date__isnull=True)

    for record in due_soon:
        user = record.student.user_profile.user  # User object
        email = user.email

        if email:
            send_mail(
                subject='📅 Reminder: Book Due Tomorrow',
                message=(
                    f"Hi {user.username},\n\n"
                    f'Your borrowed book "{record.book_copy.book.title}" is due tomorrow ({record.due_date}).\n'
                    "Please return it on time to avoid fines.\n\n"
                    "Thank you,\nLibrary Team"
                ),
                from_email='noreply@library.com', 
                recipient_list=[email],
                fail_silently=False
            )


        available_copy.status = 'borrowed'
        available_copy.save()

        messages.success(request, '✅ Book borrowed successfully.')
        return redirect('books:book_list')



class ReturnBookView(LoginRequiredMixin, View):
    def get(self, request, record_id):
        record = get_object_or_404(BorrowRecord, id=record_id)
        if record.return_date:
            return render(request, 'books/error.html', {'message': '❌ Book already returned.'})

        record.return_date = date.today()
        record.save()

        book_copy = record.book_copy
        book_copy.status = 'available'
        book_copy.save()

        if record.return_date > record.due_date:
            fine_amount = record.get_fine_amount()
            Fine.objects.create(borrow_record=record, amount=fine_amount, paid=False)

        messages.success(request, '✅ Book returned successfully.')
        return redirect('books:my_borrowed_books')


class BookRecommendationView(LoginRequiredMixin, View):
    def get(self, request):
        books = Book.objects.filter(recommended=True)
        return render(request, 'books/recommendations.html', {'books': books})


class MyFinesView(LoginRequiredMixin, View):
    def get(self, request):
        user_profile = get_object_or_404(UserProfile, user=request.user)
        student = get_object_or_404(Student, user_profile=user_profile)
        fines = Fine.objects.filter(borrow_record__student=student)
        return render(request, 'books/fines.html', {'fines': fines})


@method_decorator(staff_member_required, name='dispatch')
class ExportBorrowRecordsCSV(View):
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="borrow_records.csv"'
        writer = csv.writer(response)
        writer.writerow(['Student', 'Book Title', 'Borrow Date', 'Due Date', 'Return Date', 'Overdue','Fine Amount', 'Paid'])

        records = BorrowRecord.objects.select_related('student', 'book_copy__book').all()
        for record in records:
            student_name = record.student.user_profile.user.username
            title = record.book_copy.book.title
            borrow_date = record.borrow_date
            due_date = record.due_date
            return_date = record.return_date if record.return_date else ''
            overdue = 'Yes' if not record.return_date and date.today() > due_date else 'No'
            fine = Fine.objects.filter(borrow_record=record).first()
            fine_amount = fine.amount if fine else 0
            paid_status = 'Yes' if fine and fine.paid else 'No'
            writer.writerow([student_name, title, borrow_date, due_date, return_date, overdue, fine_amount, paid_status])
        return response


class BookCopiesView(LoginRequiredMixin, View):
    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        copies = BookCopy.objects.filter(book=book)
        return render(request, 'books/book_copies.html', {
            'book': book,
            'copies': copies
        })


class MyBorrowedBooksView(LoginRequiredMixin, View):
    def get(self, request):
        user_profile = get_object_or_404(UserProfile, user=request.user)
        student = get_object_or_404(Student, user_profile=user_profile)
        borrow_records = BorrowRecord.objects.filter(student=student, return_date__isnull=True)
        return render(request, 'books/my_borrowed_books.html', {
            'borrow_records': borrow_records
        })


@method_decorator(staff_member_required, name='dispatch')
class ExportBooksCSV(View):
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="books.csv"'
        writer = csv.writer(response)
        writer.writerow(['Title', 'Author(s)', 'ISBN'])
        for book in Book.objects.all():
            writer.writerow([book.title, ', '.join([a.name for a in book.authors.all()]), book.isbn])
        return response


class UserDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_staff:
            return render(request, 'books/staff_dashboard.html')

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            student = Student.objects.get(user_profile=user_profile)
        except (UserProfile.DoesNotExist, Student.DoesNotExist):
            return render(request, 'books/error.html', {
                'message': '⚠️ Access Denied\n❌ Student profile not found.'
            })

        borrowed_books = BorrowRecord.objects.filter(student=student)
        pending_books = borrowed_books.filter(return_date__isnull=True)
        returned_books = borrowed_books.exclude(return_date__isnull=True)

        fines = Fine.objects.filter(borrow_record__student=student)
        unpaid_fines = fines.filter(paid=False)

        subscription = StudentSubscription.objects.filter(student=student).last()
        is_expired = False
        if subscription:
            expiry_date = subscription.start_date + timedelta(days=subscription.plan.duration_days)
            if date.today() > expiry_date:
                is_expired = True

        return render(request, 'books/user_dashboard.html', {
            'borrowed_books': borrowed_books,
            'pending_books': pending_books,
            'returned_books': returned_books,
            'fines': fines,
            'unpaid_fines': unpaid_fines,
            'subscription': subscription,
            'total_borrowed': borrowed_books.count(),
            'total_returned': returned_books.count(),
            'total_pending': pending_books.count(),
            'total_fines': sum(f.amount for f in fines),
            'pending_fines': sum(f.amount for f in unpaid_fines),
            'is_expired': is_expired,
        })


@method_decorator(staff_member_required, name='dispatch')
class SendDueRemindersView(View):
    def get(self, request):
        today = date.today()
        due_records = BorrowRecord.objects.filter(return_date__isnull=True, due_date__lt=today)

        for record in due_records:
            student = record.student
            email = student.user_profile.user.email
            book_title = record.book_copy.book.title

            send_mail(
                subject='📚 Book Due Reminder',
                message=f'Hello {student.user_profile.user.username},\n\nThe book "{book_title}" is overdue.\nPlease return it as soon as possible to avoid fines.',
                from_email='library@example.com',
                recipient_list=[email],
                fail_silently=True
            )

        messages.success(request, '✅ Due reminders sent successfully.')
        return redirect('books:book_list')

@method_decorator(staff_member_required, name='dispatch')
class UploadBulkBooksView(View):
    def get(self, request):
        return render(request, 'books/upload_bulk_books.html')

    def post(self, request):
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, '❌ No file uploaded.')
            return redirect('books:upload_bulk_books')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, '❌ File is not CSV.')
            return redirect('books:upload_bulk_books')

        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            for row in reader:
                title = row.get('title')
                isbn = row.get('isbn')
                authors = row.get('authors', '').split(',')
                category = row.get('category')

                if not title or not isbn:
                    continue

                book, created = Book.objects.get_or_create(title=title, isbn=isbn)
                for name in authors:
                    author_obj, _ = book.authors.get_or_create(name=name.strip())
                if category:
                    from books.models import Category
                    cat_obj, _ = Category.objects.get_or_create(name=category)
                    book.category = cat_obj
                book.save()

            messages.success(request, '✅ Books uploaded successfully.')
            return redirect('books:book_list')

        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return redirect('books:upload_bulk_books')
