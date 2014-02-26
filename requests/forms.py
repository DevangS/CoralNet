from django import forms

class RequestInviteForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    username = forms.CharField()
    affiliation = forms.CharField()
    reason = forms.CharField(widget=forms.Textarea)
    project_description = forms.CharField(widget=forms.Textarea)
    how_did_you_hear_about_us = forms.CharField()
