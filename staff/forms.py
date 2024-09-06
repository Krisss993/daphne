from django import forms

from cart.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'title',
            'description',
            'price',
            'primary_category',
            'available_colours',
            'available_sizes',

        ]
