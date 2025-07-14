from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import SignupView, UserProfileView, EditProfileView  # ✅ CBV import करा

app_name = 'iam'

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),  # ✅ CBV
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),  # ✅ CBV
    path('edit-profile/', EditProfileView.as_view(), name='edit_profile'),  # ✅ CBV
]
