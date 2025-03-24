from django import forms
from django.contrib.auth.models import User
from .models import Auction, Bid
from .models import UserProfile

class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password", widget=forms.PasswordInput, min_length=8
    )
    password2 = forms.CharField(
        label="Confirm Password", widget=forms.PasswordInput, min_length=8
    )

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2

class AuctionForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),  # ✅ Adds date-time picker
        input_formats=['%Y-%m-%dT%H:%M']  # Ensures correct format
    )

    class Meta:
        model = Auction
        fields = ['title', 'description', 'starting_price', 'deadline']

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']

class ProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField()  # Add email field from User model
    first_name = forms.CharField(max_length=30)  # Add first name
    last_name = forms.CharField(max_length=30)  # Add last name

    class Meta:
        model = UserProfile
        fields = ['profile_picture']  # Only include fields from UserProfile

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['email'].initial = self.instance.user.email
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super(ProfileUpdateForm, self).save(commit=False)
        user = profile.user
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            profile.save()
            user.save()

        return profile