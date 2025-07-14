from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import SignupForm, UserForm, UserProfileForm
from .models import UserProfile


# ✅ 1️⃣ Signup View - Class Based
class SignupView(View):
    def get(self, request):
        user_form = SignupForm()
        profile_form = UserProfileForm()
        return render(request, 'iam/signup.html', {
            'user_form': user_form,
            'profile_form': profile_form
        })

    def post(self, request):
        user_form = SignupForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            user.email = profile.email
            user.save()

            login(request, user)
            messages.success(request, "🎉 Signup successful. Welcome!")
            return redirect('iam:profile')
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
            return render(request, 'iam/signup.html', {
                'user_form': user_form,
                'profile_form': profile_form
            })


# ✅ 2️⃣ User Profile View - Class Based
class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            messages.error(request, "⚠️ Profile not found.")
            return redirect('iam:signup')

        return render(request, 'iam/profile.html', {
            'profile': profile,
            'user': request.user,
        })


# ✅ 3️⃣ Edit Profile View - Class Based
class EditProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user_profile = get_object_or_404(UserProfile, user=request.user)
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)

        return render(request, 'iam/edit_profile.html', {
            'user_form': user_form,
            'form': profile_form
        })

    def post(self, request):
        user_profile = get_object_or_404(UserProfile, user=request.user)
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            profile.save()

            request.user.email = profile.email
            request.user.save()

            messages.success(request, "✅ Profile updated successfully.")
            return redirect('iam:profile')
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
            return render(request, 'iam/edit_profile.html', {
                'user_form': user_form,
                'form': profile_form
            })
