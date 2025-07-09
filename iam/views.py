from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, UserForm, UserProfileForm
from .models import UserProfile
from django.contrib import messages

# Signup View
def signup_view(request):
    if request.method == 'POST':
        user_form = SignupForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            # Optional: update User.email from profile
            user.email = profile.email
            user.save()

            login(request, user)
            messages.success(request, "🎉 Signup successful. Welcome!")
            return redirect('iam:profile')
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
    else:
        user_form = SignupForm()
        profile_form = UserProfileForm()

    return render(request, 'iam/signup.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


# User Profile View
@login_required
def user_profile(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, "⚠️ Profile not found.")
        return redirect('iam:signup')

    return render(request, 'iam/profile.html', {
        'profile': profile,
        'user': request.user,
    })


# Edit Profile View
@login_required
def edit_profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    user = request.user

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            profile.save()

            # Optional: update User.email from profile
            user.email = profile.email
            user.save()

            messages.success(request, "✅ Profile updated successfully.")
            return redirect('iam:profile')
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=user_profile)

    return render(request, 'iam/edit_profile.html', {
        'user_form': user_form,
        'form': profile_form
    })
