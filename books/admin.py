from django.contrib import admin
from .models import Category, Book, BookCopy, BorrowRecord, Author, Fine

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'location']
    search_fields = ['name']
    ordering = ['name']

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'isbn', 'published_date', 'recommended', 'category']
    list_filter = ['category', 'recommended']
    search_fields = ['title', 'isbn']
    filter_horizontal = ['authors']
    ordering = ['title']

@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    # ✅ Updated: removed 'no_of_copies', added 'copy_id', 'library_location'
    list_display = ['book', 'copy_id', 'status', 'library_location']  # ✅ Updated line
    list_filter = ['status', 'library_location']
    search_fields = ['book__title', 'copy_id']
    ordering = ['book']

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'book_copy', 'borrow_date', 'due_date', 'return_date']
    list_filter = ['borrow_date', 'due_date', 'return_date']
    search_fields = [
        'student__user_profile__user__username',
        'book_copy__book__title'
    ]
    ordering = ['-borrow_date']
    readonly_fields = ['borrow_date']

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ['borrow_record', 'amount', 'paid']
    list_filter = ['paid']
    search_fields = ['borrow_record__student__user_profile__user__username']
    ordering = ['-amount']
