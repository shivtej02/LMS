from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.db.models import Q
from datetime import timedelta, date

from .models import Book, BookCopy, BorrowRecord, Fine
from iam.models import Student, UserProfile
from subscription.models import StudentSubscription

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
import csv
from django.contrib.auth.models import User


# 🔹 Book List View
@login_required
def book_list(request):
    books = Book.objects.all()
    book_data = []
    for book in books:
        # ✅ Updated: use available_copies_count method
        available_copies = book.available_copies_count()  # ✅ AVAILABLE COPIES COUNT
        copies = BookCopy.objects.filter(book=book)
        book_data.append({
            'book': book,
            'available_copies': available_copies,  # ✅ pass available copies
            'copies': copies
        })
    return render(request, 'books/book_list.html', {'book_data': book_data})


# 🔹 Book Search View
@login_required
def search_books(request):
    query = request.GET.get('q', '')
    user_profile = get_object_or_404(UserProfile, user=request.user)
    student = get_object_or_404(Student, user_profile=user_profile)
    subscription = StudentSubscription.objects.filter(student=student).last()
    books = Book.objects.filter(allowed_in_plans=subscription.plan) if subscription else Book.objects.none()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(authors__name__icontains=query) |
            Q(isbn__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()

    book_data = []
    for book in books:
        # ✅ Updated: use available_copies_count method
        available_copies = book.available_copies_count()  # ✅ AVAILABLE COPIES COUNT
        copies = BookCopy.objects.filter(book=book)
        book_data.append({'book': book, 'available_copies': available_copies, 'copies': copies})

    return render(request, 'books/search_results.html', {
        'books': books,
        'query': query,
        'book_data': book_data
    })


# 🔹 Borrow View
@login_required
def borrow_book(request, copy_id):
    book_copy = get_object_or_404(BookCopy, id=copy_id)
    if book_copy.status != 'available':
        return render(request, 'books/error.html', {'message': '❌ Book not available.'})

    user_profile = get_object_or_404(UserProfile, user=request.user)
    student = get_object_or_404(Student, user_profile=user_profile)

    subscription = StudentSubscription.objects.filter(student=student).last()
    is_expired = False

    if subscription:
        expiry_date = subscription.start_date + timedelta(days=subscription.plan.duration_days)
        if date.today() > expiry_date:
           is_expired = True
    if not subscription:
        return render(request, 'books/error.html', {'message': '❌ You must subscribe to a plan before borrowing.'})

    active_borrows = BorrowRecord.objects.filter(student=student, return_date__isnull=True).count()
    if active_borrows >= subscription.plan.max_books:
        return render(request, 'books/error.html', {
            'message': f'❌ You have reached your limit of {subscription.plan.max_books} books.'
        })

    BorrowRecord.objects.create(
        student=student,
        book_copy=book_copy,
        borrow_date=date.today(),
        due_date=date.today() + timedelta(days=7),
    )

    book_copy.status = 'borrowed'
    book_copy.save()

    messages.success(request, '✅ Book borrowed successfully.')
    return redirect('book_list')


# 🔹 Return Book View
@login_required
def return_book(request, record_id):
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


# 🔹 Recommendation View
@login_required
def book_recommendation(request):
    books = Book.objects.filter(recommended=True)
    return render(request, 'books/recommendations.html', {'books': books})


# 🔹 ✅ My Fines View (Fixed version)
@login_required
def my_fines(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    student = get_object_or_404(Student, user_profile=user_profile)

    fines = Fine.objects.filter(borrow_record__student=student)

    return render(request, 'books/fines.html', {'fines': fines})


# 🔹 Export Borrow Records as CSV (Admin only)
@staff_member_required  
def export_borrow_records_csv(request):
    response = HttpResponse(content_type='text/csv') 
    response['Content-Disposition'] = 'attachment; filename="borrow_records.csv"'  

    writer = csv.writer(response)
    writer.writerow(['Student', 'Book Title', 'Borrow Date', 'Due Date', 'Return Date', 'Overdue'])

    records = BorrowRecord.objects.select_related('student', 'book_copy__book').all()

    for record in records:
        student_name = record.student.user_profile.user.username
        title = record.book_copy.book.title
        borrow_date = record.borrow_date
        due_date = record.due_date
        return_date = record.return_date if record.return_date else ''
        overdue = 'Yes' if not record.return_date and date.today() > due_date else 'No'

        writer.writerow([student_name, title, borrow_date, due_date, return_date, overdue])

    return response


# 🔹 View Copies of a Book
@login_required
def book_copies_view(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    copies = BookCopy.objects.filter(book=book)
    return render(request, 'books/book_copies.html', {
        'book': book,
        'copies': copies
    })


# 🔹 My Borrowed Books
@login_required
def my_borrowed_books(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    student = get_object_or_404(Student, user_profile=user_profile)
    borrow_records = BorrowRecord.objects.filter(student=student, return_date__isnull=True)
    return render(request, 'books/my_borrowed_books.html', {
        'borrow_records': borrow_records
    })


# 🔹 Export Books CSV (Admin only)
@staff_member_required
def export_books_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="books.csv"'
    writer = csv.writer(response)
    writer.writerow(['Title', 'Author(s)', 'ISBN'])
    for book in Book.objects.all():
        writer.writerow([book.title, ', '.join([a.name for a in book.authors.all()]), book.isbn])
    return response


# 🔹 User Dashboard
@login_required
def user_dashboard(request):
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


# 🔹 Send Due Reminders
@staff_member_required
def send_due_reminders(request):
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
