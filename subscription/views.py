from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import SubscriptionPlan, StudentSubscription, Fine, BulkUpload
from iam.models import Student
from .forms import FinePaymentForm


# 🔹 Select Subscription Plan
@login_required
def select_subscription_plan(request):
    plans = SubscriptionPlan.objects.all()

    try:
        student = Student.objects.get(user_profile__user=request.user)
    except Student.DoesNotExist:
        return render(request, 'books/error.html', {'message': '⚠️ Student profile not found.'})

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        if plan_id:
            plan = get_object_or_404(SubscriptionPlan, id=plan_id)

            # 🔍 Check if student already has active subscription
            active_sub = StudentSubscription.objects.filter(
                student=student
            ).order_by('-start_date').first()

            if active_sub:
                expiry = active_sub.start_date + timezone.timedelta(days=active_sub.plan.duration_days)
                if expiry >= timezone.now().date():
                    # ❌ Already active plan, don't allow new
                    messages.warning(
                        request,
                        f'⚠️ You already have an active plan: {active_sub.plan.name} valid till {expiry}.'
                    )
                    return redirect('subscription:my_subscription')

            # ✅ Remove expired old subscriptions (cleanup)
            StudentSubscription.objects.filter(student=student).delete()

            # ✅ Create new subscription
            StudentSubscription.objects.create(
                student=student,
                plan=plan,
                start_date=timezone.now().date()
            )

            messages.success(request, f"🎉 Congrats! You subscribed to {plan.name} plan successfully.")
            return redirect('subscription:my_subscription')

    return render(request, 'subscription/select_plan.html', {'plans': plans})



# 🔹 View My Subscription
@login_required
def my_subscription(request):
    try:
        student = Student.objects.get(user_profile__user=request.user)
    except Student.DoesNotExist:
        return render(request, 'books/error.html', {'message': '⚠️ Student profile not found.'})

    subscription = StudentSubscription.objects.filter(student=student).last()
    return render(request, 'subscription/my_subscription.html', {'subscription': subscription})


# 🔹 Pay Fines
@login_required
def pay_fine(request):
    try:
        student = Student.objects.get(user_profile__user=request.user)
    except Student.DoesNotExist:
        return render(request, 'books/error.html', {'message': '⚠️ Student profile not found.'})

    unpaid_fines = Fine.objects.filter(borrow_record__student=student, paid=False)

    if request.method == 'POST':
        form = FinePaymentForm(request.POST)
        if form.is_valid():
            record_id = form.cleaned_data['record_id']
            try:
                fine = Fine.objects.get(borrow_record__id=record_id)
                fine.paid = True
                fine.save()
                messages.success(request, '✅ Fine paid successfully.')
            except Fine.DoesNotExist:
                messages.error(request, '❌ Fine record not found.')
            return redirect('subscription:pay_fine')
    else:
        form = FinePaymentForm()

    return render(request, 'subscription/pay_fine.html', {
        'fines': unpaid_fines,
        'form': form
    })


# 🔹 Upload Bulk Books (for Staff Only)
@login_required
def upload_bulk_books(request):
    # ✅ Check if user is staff
    if not hasattr(request.user, 'userprofile') or not hasattr(request.user.userprofile, 'staffprofile'):
        return render(request, 'books/error.html', {
            'message': '❌ Only staff members can upload books.'
        })

    if request.method == 'POST':
        uploaded_file = request.FILES.get('upload_file')
        if uploaded_file:
            staff_profile = request.user.userprofile.staffprofile
            BulkUpload.objects.create(uploaded_by=staff_profile, upload_file=uploaded_file)
            messages.success(request, '✅ File uploaded successfully.')
            return redirect('subscription:upload_bulk_books')

    return render(request, 'subscription/upload_bulk_books.html')
