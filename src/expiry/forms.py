from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date , time

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
        widget=forms.PasswordInput(attrs={
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

        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username or password.")
            cleaned_data['user'] = user

        return cleaned_data

class AddItem(forms.Form):
    item_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder': 'Enter item name'
        })
    )

    item_category = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder': 'e.g., Fruit, Dairy, Vegetables'
        })
    )

    quantity = forms.IntegerField(
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder': 'Quantity'
        })
    )

    expiry_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class':    'border w-full text-base px-2 py-1 focus:outline-none '\
                        'focus:ring-0 focus:border-green-600 rounded-xl',
            'placeholder': 'YYYY-MM-DD',
            'type': 'date',
        })
    )     


    def clean(self):
        cleaned_data = super().clean()
        expiry_date = cleaned_data.get('expiry_date')

        if expiry_date and expiry_date < date.today():   #Incase it is none uses an and so comparison doesn't execute as it is false
            raise forms.ValidationError("Expiry date cannot be in the past")

        return cleaned_data

class SettingsForm(forms.Form):

    Days = [
        (0, 'Mon'),
        (1, 'Tue'),
        (2, 'Wed'),
        (3, 'Thu'),
        (4, 'Fri'),
        (5, 'Sat'),
        (6, 'Sun'),
    ]

    notification_days = forms.MultipleChoiceField(
        choices=Days,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'w-4 h-4 text-green-600 bg-neutral-secondary-medium border-default-medium rounded focus:ring-green-500 focus:ring-2'
        }),
        required=False,
    )

    notification_time = forms.TimeField(
        required=False  ,
        widget=forms.TimeInput(attrs={}),
        initial = time(9,30)
    )

    notifications = forms.BooleanField(
        required=False,
        initial=True,
        label='Notifications'
    )
    dark_mode = forms.BooleanField(
        required=False,
        initial=False,
        label='Dark Mode'
    )