from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from books.models import BorrowRecord

class Command(BaseCommand):
    help = 'Send reminder emails for due books'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        due_records = BorrowRecord.objects.filter(due_date__lte=today, return_date__isnull=True)

        if not due_records.exists():
            self.stdout.write("✅ No due books found. No reminders sent.")
            return

        for record in due_records:
            student = record.student
            user = student.user_profile.user  # ✅ user fetched from UserProfile

            email = getattr(user, 'email', None)
            print(f"Checking email for student ID {student.id}: {email}")

            if not email:
                self.stdout.write(
                    f"⚠️ Skipped: No email found for student ID {student.id}, username: {user.username}"
                )
                continue

            first_name = user.first_name
            book_title = record.book_copy.book.title
            due_date = record.due_date

            subject = f"📚 Reminder: Book '{book_title}' is due!"
            message = (
                f"Dear {first_name},\n\n"
                f"This is a friendly reminder that the book '{book_title}' was due on {due_date}.\n"
                "Please return it as soon as possible to avoid any late fines.\n\n"
                "Thank you,\n"
                "Library Management System"
            )

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            self.stdout.write(f"📧 Reminder sent to {email} for book: '{book_title}'")
