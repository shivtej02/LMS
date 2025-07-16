from django.urls import path
from .views import (
    BookListView,
    BookSearchView,
    BorrowBookView,
    ReturnBookView,
    BookRecommendationView,
    MyFinesView,
    SendDueRemindersView,
    BookCopiesView,
    MyBorrowedBooksView,
    ExportBooksCSV,
    UserDashboardView,
    ExportBorrowRecordsCSV,
    BookDetailView,
)
app_name = 'books'

urlpatterns = [
    path('book-list/', BookListView.as_view(), name='book_list'),
    path('borrow/<int:book_id>/', BorrowBookView.as_view(), name='borrow_book'),
    path('return/<int:record_id>/', ReturnBookView.as_view(), name='return_book'),
    path('search/', BookSearchView.as_view(), name='search_books'),
    path('recommend/', BookRecommendationView.as_view(), name='book_recommendation'),
    path('my-fines/', MyFinesView.as_view(), name='my_fines'),
    path('send-reminders/', SendDueRemindersView.as_view(), name='send_reminders'),
    path('book/<int:book_id>/copies/', BookCopiesView.as_view(), name='book_copies'),
    path('my-borrowed-books/', MyBorrowedBooksView.as_view(), name='my_borrowed_books'),
    path('export-books/', ExportBooksCSV.as_view(), name='export_books'),
    path('dashboard/', UserDashboardView.as_view(), name='user_dashboard'),
    path('export/borrow-records/', ExportBorrowRecordsCSV.as_view(), name='export_borrow_records'),
    path('book/<int:book_id>/detail/', BookDetailView.as_view(), name='book_detail'),  
]
