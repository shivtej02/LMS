from django.contrib import admin
from .models import SubscriptionPlan, StudentSubscription, Fine, BulkUpload

admin.site.register(SubscriptionPlan)
admin.site.register(StudentSubscription)
admin.site.register(Fine)
admin.site.register(BulkUpload)
