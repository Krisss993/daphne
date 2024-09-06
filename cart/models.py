from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.utils.text import slugify
from django.shortcuts import reverse

User = get_user_model()


class ColourVariation(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class SizeVariation(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Address(models.Model):
    ADDRESS_CHOICES = (
        ('B', 'billing'),
        ('S', 'shipping'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_line_1 = models.CharField(max_length=150)
    address_line_2 = models.CharField(max_length=150)
    zip_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line_1}, {self.address_line_2}, {self.city}, {self.zip_code}"

    class Meta:
        verbose_name_plural = 'Addresses'


class Delivery(models.Model):
    type = models.CharField(max_length=60)
    cost = models.IntegerField(default=0)

    def get_total(self):
        return '{:.2f}'.format(self.cost / 100)

    def __str__(self):
        return f'{self.type} - {self.get_total()} zł'

    class Meta:
        verbose_name_plural = 'Deliveries'


class Order(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(blank=True, null=True)
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey(Address, related_name='billing_address', blank=True, null=True,
                                        on_delete=models.SET_NULL)
    shipping_address = models.ForeignKey(Address, related_name='shipping_address', blank=True, null=True,
                                         on_delete=models.SET_NULL)
    delivery = models.ForeignKey('Delivery', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"ORDER-{self.pk}"

    def get_raw_subtotal(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_raw_total_item_price()
        return total

    def get_subtotal(self):
        subtotal = self.get_raw_subtotal()
        return '{:.2f}'.format(subtotal / 100)

    def get_raw_total(self):
        if self.delivery is None:
            total = self.get_raw_subtotal()
        else:
            total = self.get_raw_subtotal() + self.delivery.cost
        return total

    def get_total(self):
        total = self.get_raw_total()
        return '{:.2f}'.format(total / 100)

    @property
    def reference_number(self):
        return f"ORDER-{self.pk}"


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=(
        ('paypal', 'PayPal'),
    ))
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    amount = models.FloatField()
    raw_response = models.TextField()

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f"PAYMENT-{self.order}-{self.pk}"


class Product(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='product_images', blank=True, null=True)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    available_colours = models.ManyToManyField(ColourVariation)
    available_sizes = models.ManyToManyField(SizeVariation)
    price = models.IntegerField(default=0)
    primary_category = models.ForeignKey('Category', related_name='primary_products', on_delete=models.CASCADE)
    secondary_categories = models.ManyToManyField('Category', blank=True)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Product: {self.title}>"

    def get_absolute_url(self):
        return reverse('cart:product-detail', kwargs={'slug': self.slug})

    def get_price(self):
        return '{:.2f}'.format(self.price / 100)

    def get_delete_url(self):
        return reverse('staff:product-delete', kwargs={'pk': self.pk})

    def get_update_url(self):
        return reverse('staff:product-update', kwargs={'pk': self.pk})

    @property
    def in_stock(self):
        return self.stock > 0


def pre_save_product_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.title)


pre_save.connect(pre_save_product_receiver, sender=Product)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    colour = models.ForeignKey(ColourVariation, on_delete=models.CASCADE)
    size = models.ForeignKey(SizeVariation, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    def get_raw_total_item_price(self):
        return self.quantity * self.product.price

    def get_total_item_price(self):
        return '{:.2f}'.format(self.get_raw_total_item_price() / 100)


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
