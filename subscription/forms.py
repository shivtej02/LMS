from django import forms
from .models import SubscriptionPlan

class SubscriptionSelectForm(forms.Form):
    plan_id = forms.IntegerField(widget=forms.HiddenInput())

class FinePaymentForm(forms.Form):
    record_id = forms.IntegerField(widget=forms.HiddenInput())
