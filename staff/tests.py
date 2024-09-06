from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from cart.models import Order, Product, Category, ColourVariation, SizeVariation
from staff.forms import ProductForm


class SetUpTests(TestCase):
    dummy_image = SimpleUploadedFile(
        name='dom.jpg',
        content=open('media/dom.jpg', 'rb').read(),
        content_type='image/jpeg'
    )

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword', is_staff=False)
        self.staff_user = User.objects.create_user(username='staffuser', password='staffpassword', is_staff=True)
        self.category = Category.objects.create(name='Test Category')
        self.product1 = Product.objects.create(title='Product 1', image=self.dummy_image,
                                               primary_category=self.category, price=100, stock=10)
        self.product2 = Product.objects.create(title='Product 2', image=self.dummy_image,
                                               primary_category=self.category, price=200, stock=5)


class StaffViewTest(SetUpTests):

    def test_staff_view_access_for_no_staff_user(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('staff:staff')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_staff_view_access_for_staff_user(self):
        order1 = Order.objects.create(user=self.staff_user, ordered=True)
        order2 = Order.objects.create(user=self.staff_user, ordered=True)
        self.client.login(username='staffuser', password='staffpassword')
        url = reverse('staff:staff')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'staff/staff.html')
        self.assertIn('orders', response.context)
        orders_in_context = response.context['orders']
        self.assertEqual(list(orders_in_context), [order1, order2])


class ProductListViewTest(SetUpTests):
    def test_product_list_view_access_for_no_staff_user(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('staff:product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_product_list_view_access_for_staff_user(self):
        self.client.login(username='staffuser', password='staffpassword')
        url = reverse('staff:product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'staff/product_list.html')
        self.assertIn('products', response.context)
        products_in_context = response.context['products']
        self.assertEqual(list(products_in_context), [self.product1, self.product2])


class ProductDeleteViewTest(SetUpTests):
    def test_product_delete_view_access_for_no_staff_user(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('staff:product-delete', kwargs={'pk': self.product1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_product_delete_view_access_for_staff_user(self):
        initial_products_nr = Product.objects.count()
        self.client.login(username='staffuser', password='staffpassword')
        url = reverse('staff:product-delete', kwargs={'pk': self.product1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('staff:product-list'))
        updated_products_nr = Product.objects.count()
        self.assertEqual(initial_products_nr - 1, updated_products_nr)


class ProductUpdateViewTest(SetUpTests):

    def test_product_update_view_access_for_no_staff_user(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('staff:product-delete', kwargs={'pk': self.product1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_product_update_view_post(self):
        self.client.login(username='staffuser', password='staffpassword')
        colour = ColourVariation.objects.create(name='White')
        size = SizeVariation.objects.create(name='Medium')
        self.product1.available_colours.add(colour)
        self.product1.available_sizes.add(size)
        url = reverse('staff:product-update', kwargs={'pk': self.product1.pk})
        updated_data = {
            'title': 'Updated Product',
            'description': 'Hello there',
            'price': 20,
            'available_colours': [colour.pk],
            'available_sizes': [size.pk],
            'primary_category': self.category.pk
        }

        form = ProductForm(data=updated_data)
        self.assertTrue(form.is_valid())
        response = self.client.post(url, data=updated_data)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.title, 'Updated Product')
        self.assertEqual(self.product1.price, 20)
        self.assertIn(colour, self.product1.available_colours.all())
        self.assertIn(size, self.product1.available_sizes.all())
        self.assertRedirects(response, reverse('staff:product-list'))


class ProductCreateViewTest(SetUpTests):

    def test_product_create_view_access_for_no_staff_user(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('staff:product-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_product_create_view_valid(self):
        self.client.login(username='staffuser', password='staffpassword')
        colour_white = ColourVariation.objects.create(name='White')
        size_medium = SizeVariation.objects.create(name='Medium')
        data = {
            'title': 'New Product',
            'description': 'Description',
            'price': 100,
            'available_colours': [colour_white.pk],
            'available_sizes': [size_medium.pk],
            'primary_category': self.category.pk
        }

        form = ProductForm(data=data)
        self.assertTrue(form.is_valid())
        starting_objects_count = Product.objects.count()
        response = self.client.post(reverse('staff:product-create'), data=data)
        created_objects_count = Product.objects.count()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(starting_objects_count, created_objects_count - 1)

    def test_product_create_view_invalid(self):
        self.client.login(username='staffuser', password='staffpassword')
        data = {}
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        response = self.client.post(reverse('staff:product-create'), data=data)
        self.assertEqual(response.status_code, 200)
