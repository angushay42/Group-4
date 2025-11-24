from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone

import logging

logger = logging.Logger('forms')

class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(
        max_length=150, 
        widget=forms.TextInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder': 'Email'
        })
    )
    first_name = forms.CharField(
        max_length=50, 
        widget=forms.TextInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder' : 'Name'
        })
    )
    last_name = forms.CharField(
        max_length=50, 
        widget=forms.TextInput(attrs={
        'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                    'focus:ring-0 focus:border-green-600 rounded-xl',
        'placeholder' : 'Surname'
        })
    )

    class Meta:
        model = User
        fields = (
            'username', 
            'first_name', 
            'last_name', 
            'email', 
            'password1', 
            'password2'
        )

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)

        # apply styling to all inherited fields
        self.fields['username'].widget.attrs.update({
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder' : 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder' : 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder' : 'Confirm Password'
        })

        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

class LogininForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder': 'Username'
        })
    )

    password = forms.CharField(
        widget=forms.TextInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder': 'Password'
        })
    )

    def clean(self):
        try:
            cleaned_data = super().clean()
        except ValidationError as e:
            logger.debug(
                "error at {}: {}".format(timezone.now(), e)
            )

        username = cleaned_data.get('username')  # Changed from 'user' to 'username'
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username or password.")
            cleaned_data['user'] = user

        return cleaned_data

class AddItem(forms.Form):
    item_name = forms.CharField(
        max_length=150, 
        # @charlie edit if needed, I just copied
        widget=forms.TextInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder': 'Item'
        })
    )

    expiry_date = forms.DateField(  # unsure if any other params are needed
        widget=forms.TextInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder': 'Expiry date'
        })
    )     
    quantity = forms.IntegerField(
        min_value=1,
        required=True,
        widget=forms.TextInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder': 'Quantity'
        })
    )


    