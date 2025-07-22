import schedule
import time
import os
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LibraryProject.settings')
django.setup()

def job():
    print("🔁 Running send_reminders command...")
    os.system("python manage.py send_reminders")

# Run daily at 10:00 AM
schedule.every().day.at("10:00").do(job)

print("📅 Reminder Scheduler Started... Waiting for 10:00 AM")

while True:
    schedule.run_pending()
    time.sleep(60)
