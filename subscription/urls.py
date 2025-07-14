from django.urls import path
from .views import (
    SelectSubscriptionPlanView,
    MySubscriptionView,
    PayFineView,
    UploadBulkBooksView,
)

app_name = 'subscription'

urlpatterns = [
    path('select-plan/', SelectSubscriptionPlanView.as_view(), name='select_plan'),
    path('my-subscription/', MySubscriptionView.as_view(), name='my_subscription'),
    path('pay-fine/', PayFineView.as_view(), name='pay_fine'),
    path('upload-bulk-books/', UploadBulkBooksView.as_view(), name='upload_bulk_books'),
]
