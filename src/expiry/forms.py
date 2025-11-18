from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User


class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(widget=forms.TextInput(attrs={
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