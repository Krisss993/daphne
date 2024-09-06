from django import forms


class ContactForm(forms.Form):
    imię = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'Twoje imię'
    }))
    email = forms.EmailField(widget=forms.TextInput(attrs={
        'placeholder': 'Twój email'
    }))
    wiadomość = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Twoja wiadomość'
    }))
