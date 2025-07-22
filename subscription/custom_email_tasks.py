# ✅ FILE: subscription/custom_email_tasks.py

from datetime import timedelta, date
from django.core.mail import send_mail
from books.models import BorrowRecord


def send_due_soon_reminders():
    """
    📅 Sends reminder emails for books due tomorrow.
    Called manually or via cron/command.
    """
    today = date.today()
    reminder_date = today + timedelta(days=1)  # Target books due tomorrow

    # Only borrowed books not yet returned
    records = BorrowRecord.objects.filter(return_date__isnull=True, due_date=reminder_date)

    for record in records:
        user = record.student.user_profile.user
        if user.email:
            send_mail(
                subject="📚 Reminder: Book Due Tomorrow",
                message=(
                    f"Dear {user.first_name},\n\n"
                    f"Your borrowed book '{record.book_copy.book.title}' is due tomorrow ({record.due_date}).\n"
                    "Please return it on time to avoid any fine.\n\n"
                    "Thank you,\nLibrary Management System"
                ),
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )


def send_overdue_reminders():
    """
    📧 Sends DAILY email reminders for books overdue by 3+ days and not yet returned.
    """
    today = date.today()
    overdue_threshold = today - timedelta(days=3)

    # Target books that are overdue for 3 or more days
    records = BorrowRecord.objects.filter(return_date__isnull=True, due_date__lte=overdue_threshold)

    for record in records:
        user = record.student.user_profile.user
        if user.email:
            send_mail(
                subject="⚠️ Overdue Book Alert",
                message=(
                    f"Dear {user.first_name},\n\n"
                    f"Your borrowed book '{record.book_copy.book.title}' was due on {record.due_date} and is now overdue.\n"
                    "Please return it as soon as possible to avoid more fines.\n\n"
                    "Thank you,\nLibrary Management System"
                ),
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )
