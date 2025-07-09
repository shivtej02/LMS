# subscription/urls.py

from django.urls import path
from . import views

app_name = 'subscription'

urlpatterns = [
    path('select-plan/', views.select_subscription_plan, name='select_plan'),
    path('my-subscription/', views.my_subscription, name='my_subscription'),
    path('pay-fine/', views.pay_fine, name='pay_fine'),
    path('upload-bulk-books/', views.upload_bulk_books, name='upload_bulk_books'),
]
