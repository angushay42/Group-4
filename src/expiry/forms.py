from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(max_length=150,widget=forms.TextInput(attrs={
        'class': 'border w-full text-base px-2 py-1 focus:outline-none focus:ring-0 focus:border-green-600 rounded-xl'
    }))
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'border w-full text-base px-2 py-1 focus:outline-none focus:ring-0 focus:border-green-600 rounded-xl'
    }))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'border w-full text-base px-2 py-1 focus:outline-none focus:ring-0 focus:border-green-600 rounded-xl'
    }))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs): # apply styling to all inherited fields
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'border w-full text-base px-2 py-1 focus:outline-none focus:ring-0 focus:border-green-600 rounded-xl'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'border w-full text-base px-2 py-1 focus:outline-none focus:ring-0 focus:border-green-600 rounded-xl'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'border w-full text-base px-2 py-1 focus:outline-none focus:ring-0 focus:border-green-600 rounded-xl'
        })

class LogininForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'border w-full text-base px-2 py-1 focus:outline-none focus:ring-0 focus:border-green-600 rounded-xl',
        'placeholder': 'Username'
    }))

    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'border w-full text-base px-2 py-1 focus:outline-none focus:ring-0 focus:border-green-600 rounded-xl',
        'placeholder': 'Password'
    }))

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')  # Changed from 'user' to 'username'
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username or password.")
            cleaned_data['user'] = user

        return cleaned_data
