# forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Note, Task, Meeting

class SignupForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'year', 'department', 'division','subject']

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.first_name = self.cleaned_data['first_name']
        profile.last_name = self.cleaned_data['last_name']
        if commit:
            profile.save()
        return profile


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'description', 'file']


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title']

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['scheduled_time', 'description']