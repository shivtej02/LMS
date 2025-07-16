from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, FormView
import csv, io
from .models import SubscriptionPlan, StudentSubscription, Fine, BulkUpload
from iam.models import Student
from .forms import FinePaymentForm
from books.models import Book, Author, Category, BookCopy 

# 🔹 Select Subscription Plan
class SelectSubscriptionPlanView(LoginRequiredMixin, View):
    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        try:
            student = Student.objects.get(user_profile__user=request.user)
        except Student.DoesNotExist:
            return render(request, 'books/error.html', {'message': '⚠️ Student profile not found.'})

        return render(request, 'subscription/select_plan.html', {'plans': plans})

    def post(self, request):
        plans = SubscriptionPlan.objects.all()
        try:
            student = Student.objects.get(user_profile__user=request.user)
        except Student.DoesNotExist:
            return render(request, 'books/error.html', {'message': '⚠️ Student profile not found.'})

        plan_id = request.POST.get('plan_id')
        if plan_id:
            plan = get_object_or_404(SubscriptionPlan, id=plan_id)

            active_sub = StudentSubscription.objects.filter(
                student=student
            ).order_by('-start_date').first()

            if active_sub:
                expiry = active_sub.start_date + timezone.timedelta(days=active_sub.plan.duration_days)
                if expiry >= timezone.now().date():
                    messages.warning(
                        request,
                        f'⚠️ You already have an active plan: {active_sub.plan.name} valid till {expiry}.'
                    )
                    return redirect('subscription:my_subscription')

            StudentSubscription.objects.filter(student=student).delete()

            StudentSubscription.objects.create(
                student=student,
                plan=plan,
                start_date=timezone.now().date()
            )

            messages.success(request, f"🎉 Congrats! You subscribed to {plan.name} plan successfully.")
            return redirect('subscription:my_subscription')

        return render(request, 'subscription/select_plan.html', {'plans': plans})

# 🔹 View My Subscription
class MySubscriptionView(LoginRequiredMixin, TemplateView):
    template_name = 'subscription/my_subscription.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = Student.objects.get(user_profile__user=self.request.user)
            subscription = StudentSubscription.objects.filter(student=student).last()
            context['subscription'] = subscription
        except Student.DoesNotExist:
            return render(self.request, 'books/error.html', {'message': '⚠️ Student profile not found.'})
        return context

# 🔹 Pay Fines
class PayFineView(LoginRequiredMixin, FormView):
    template_name = 'subscription/pay_fine.html'
    form_class = FinePaymentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = Student.objects.get(user_profile__user=self.request.user)
            unpaid_fines = Fine.objects.filter(borrow_record__student=student, paid=False)
            context['fines'] = unpaid_fines
        except Student.DoesNotExist:
            return render(self.request, 'books/error.html', {'message': '⚠️ Student profile not found.'})
        return context

    def form_valid(self, form):
        record_id = form.cleaned_data['record_id']
        try:
            fine = Fine.objects.get(borrow_record__id=record_id)
            fine.paid = True
            fine.save()
            messages.success(self.request, '✅ Fine paid successfully.')
        except Fine.DoesNotExist:
            messages.error(self.request, '❌ Fine record not found.')
        return redirect('subscription:pay_fine')

# ✅🔹 Upload Bulk Books (with CSV Parsing)
class UploadBulkBooksView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and hasattr(self.request.user.userprofile, 'staffprofile')

    def get(self, request):
        return render(request, 'subscription/upload_bulk_books.html')

    def post(self, request):
        uploaded_file = request.FILES.get('upload_file')
        if not uploaded_file:
            return render(request, 'subscription/upload_bulk_books.html', {'message': '❌ No file uploaded.'})

        decoded_file = uploaded_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.reader(io_string)
        next(reader)  # Skip header row

        added_books = 0
        for row in reader:
            try:
                title, author_name, isbn, category_name, description, published_date, copies = row

                # 🔸 Author
                author, _ = Author.objects.get_or_create(name=author_name.strip())
                
                # 🔸 Category
                category, _ = Category.objects.get_or_create(name=category_name.strip(), defaults={'location': 'Rack A'})

                # 🔸 Book
                book, created = Book.objects.get_or_create(
                    title=title.strip(),
                    isbn=isbn.strip(),
                    defaults={
                        'description': description.strip(),
                        'published_date': published_date.strip(),
                        'category': category
                    }
                )
                book.authors.add(author)

                # 🔸 Book Copies
                if created:
                    for i in range(int(copies)):
                        BookCopy.objects.create(
                            book=book,
                            copy_id=f"{isbn.strip()}-{i+1}",
                            status='available'
                        )
                added_books += 1

            except Exception as e:
                continue

        messages.success(request, f'✅ Uploaded {added_books} books successfully.')
        return redirect('subscription:upload_bulk_books')
