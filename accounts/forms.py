from django import forms

class RequestInviteForm(forms.Form):
    email = forms.EmailField()
    username = forms.CharField()
    reason = forms.CharField(widget=forms.Textarea)