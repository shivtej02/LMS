from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

app_name = 'iam'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'), 
    path('profile/', views.user_profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
]
