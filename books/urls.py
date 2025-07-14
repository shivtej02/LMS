from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('book-list/', views.book_list, name='book_list'),
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('return/<int:record_id>/', views.return_book, name='return_book'),
    path('search/', views.search_books, name='search_books'),
    path('recommend/', views.book_recommendation, name='book_recommendation'),
    path('my-fines/', views.my_fines, name='my_fines'),
    path('send-reminders/', views.send_due_reminders, name='send_reminders'),
    path('book/<int:book_id>/copies/', views.book_copies_view, name='book_copies'),
    path('my-borrowed-books/', views.my_borrowed_books, name='my_borrowed_books'),
    path('export-books/', views.export_books_csv, name='export_books'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('export/borrow-records/', views.export_borrow_records_csv, name='export_borrow_records'),
]
