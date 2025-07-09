from django import forms

class BorrowForm(forms.Form):
    copy_id = forms.IntegerField(widget=forms.HiddenInput())
