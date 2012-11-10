from django import forms

class RequestInviteForm(forms.Form):
    email = forms.EmailField()
    username = forms.CharField()
    affiliation = forms.CharField()
    reason = forms.CharField(widget=forms.Textarea)
    project_description = forms.CharField(widget=forms.Textarea)
    how_did_you_hear_about_us = forms.CharField()
