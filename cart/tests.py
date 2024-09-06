import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import TestCase, Client
from django.urls import reverse

from .models import Product, Category, ColourVariation, SizeVariation, User, Order, OrderItem, Address, Payment, \
    Delivery
from .utils import get_or_set_order_session


class ProductListViewTest(TestCase):
    dummy_image = SimpleUploadedFile(
        name='test_image.jpg',
        content=open('media/test_image.jpg', 'rb').read(),
        content_type='image/jpeg'
    )

    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product1 = Product.objects.create(title='Product 1', slug='product-1', image=self.dummy_image,
                                               primary_category=self.category, price=100, stock=10)
        self.product2 = Product.objects.create(title='Product 2', slug='product-2', image=self.dummy_image,
                                               primary_category=self.category, price=200, stock=5)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('cart:product-list'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('cart:product-list'))
        self.assertTemplateUsed(response, 'cart/product_list.html')

    def test_view_context_contains_products(self):
        response = self.client.get(reverse('cart:product-list'))
        self.assertContains(response, self.product1.title)
        self.assertContains(response, self.product2.title)

    def test_view_filters_products_by_category(self):
        category2 = Category.objects.create(name='Category 2')
        product3 = Product.objects.create(title='Product 3', slug='product-3', image=self.dummy_image,
                                          primary_category=category2, price=300, stock=15)
        response = self.client.get(reverse('cart:product-list'), {'category': self.category.name})
        self.assertContains(response, self.product1.title)
        self.assertContains(response, self.product2.title)
        self.assertNotContains(response, product3.title)

    def test_view_context_contains_categories(self):
        response = self.client.get(reverse('cart:product-list'))
        self.assertQuerysetEqual(response.context['categories'], Category.objects.all(), transform=lambda x: x)

    def test_view_context_contains_no_products_when_empty_database(self):
        Product.objects.all().delete()
        response = self.client.get(reverse('cart:product-list'))
        self.assertQuerysetEqual(response.context['object_list'], [])


class ProductDetailViewTest(TestCase):
    dummy_image = SimpleUploadedFile(
        name='test_image.jpg',
        content=open('media/test_image.jpg', 'rb').read(),
        content_type='image/jpeg'
    )

    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(title='Test Product', slug='test-product', image=self.dummy_image,
                                              price=100, stock=10, primary_category=self.category)
        self.url = reverse('cart:product-detail', kwargs={'slug': self.product.slug})
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.order = Order.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpassword')

    def test_view_url_accessible_by_name(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'cart/product_detail.html')

    def test_view_renders_correct_context(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['product'], self.product)

    def test_view_returns_404_when_product_not_found(self):
        wrong_slug = 'wrong-slug'
        wrong_url = reverse('cart:product-detail', kwargs={'slug': wrong_slug})
        response = self.client.get(wrong_url)
        self.assertEqual(response.status_code, 404)

    def test_form_valid_creates_new_cart_item(self):
        initial_item_count = self.product.orderitem_set.count()
        colour_choice = ColourVariation.objects.create(name='Red')
        size_choice = SizeVariation.objects.create(name='M')
        self.product.available_colours.add(colour_choice)
        self.product.available_sizes.add(size_choice)

        data = {
            'colour': colour_choice.id,
            'size': size_choice.id,
            'quantity': 3,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.orderitem_set.count(), initial_item_count + 1)

    def test_form_invalid_with_quantity_greater_than_stock(self):
        colour_choice = ColourVariation.objects.create(name='Red')
        size_choice = SizeVariation.objects.create(name='M')
        self.product.available_colours.add(colour_choice)
        self.product.available_sizes.add(size_choice)

        data = {
            'colour': colour_choice.id,
            'size': size_choice.id,
            'quantity': 15,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['__all__'][0], f"Maksymalna dostępna ilość to: {self.product.stock}")


class CartViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('cart:summary'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('cart:summary'))
        self.assertTemplateUsed(response, 'cart/cart.html')

    def test_cart_view_with_order(self):
        order = Order.objects.create()
        session = self.client.session
        session['order_id'] = order.id
        session.save()
        user = User.objects.create(username='testuser')
        self.client.force_login(user)
        response = self.client.get(reverse('cart:summary'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('order', response.context)
        self.assertEqual(response.context['order'], order)

    def test_get_or_set_order_session_with_authenticated_user(self):
        user = User.objects.create(username='testuser')
        self.client.force_login(user)
        response = self.client.get(reverse('cart:summary'))
        request = response.wsgi_request
        order = get_or_set_order_session(request)
        self.assertEqual(order.user, user)

    def test_get_or_set_order_session_without_authenticated_user(self):
        request = self.client.get(reverse('cart:summary')).wsgi_request
        order = get_or_set_order_session(request)
        self.assertIsNone(order.user)

    def test_get_or_set_order_session_without_existing_order(self):
        request = self.client.get(reverse('cart:summary')).wsgi_request
        request.session['order_id'] = 999
        order = get_or_set_order_session(request)
        self.assertIsInstance(order, Order)
        self.assertIsNone(order.user)
        self.assertFalse(order.ordered)
        self.assertIsNotNone(request.session.get('order_id'))


class IncreaseQuantityViewTest(TestCase):
    dummy_image = SimpleUploadedFile(
        name='test_image.jpg',
        content=open('media/test_image.jpg', 'rb').read(),
        content_type='image/jpeg'
    )

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.category = Category.objects.create(name='Test Category')
        self.colour = ColourVariation.objects.create(name='red')
        self.size = SizeVariation.objects.create(name='M')
        self.order = Order(user=self.user)
        self.order.save()
        self.product = Product.objects.create(title='Product 1', slug='product-1', image=self.dummy_image,
                                              primary_category=self.category, price=100, stock=10)
        self.order_item = OrderItem.objects.create(order=self.order, product=self.product, colour=self.colour,
                                                   size=self.size, quantity=2)
        self.url = reverse('cart:increase-quantity', kwargs={'pk': self.order_item.pk})

    def test_view_url_accessible_by_name(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_redirect(self):
        response = self.client.get(reverse('cart:increase-quantity', kwargs={'pk': self.order_item.pk}))
        self.assertRedirects(response, reverse('cart:summary'))

    def test_increase_quantity_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('cart:increase-quantity', kwargs={'pk': self.order_item.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cart:summary'))
        updated_order_item = get_object_or_404(OrderItem, pk=self.order_item.pk)
        self.assertEqual(updated_order_item.quantity, self.order_item.quantity + 1)


class DecreaseQualityViewTest(TestCase):
    dummy_image = SimpleUploadedFile(
        name='test_image.jpg',
        content=open('media/test_image.jpg', 'rb').read(),
        content_type='image/jpeg'
    )

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.category = Category.objects.create(name='Test Category')
        self.colour = ColourVariation.objects.create(name='red')
        self.size = SizeVariation.objects.create(name='M')
        self.order = Order(user=self.user)
        self.order.save()
        self.product = Product.objects.create(title='Product 1', slug='product-1', image=self.dummy_image,
                                              primary_category=self.category, price=100, stock=10)
        self.order_item = OrderItem.objects.create(order=self.order, product=self.product, colour=self.colour,
                                                   size=self.size, quantity=2)

    def test_decrease_quantity_view(self):
        order_item = OrderItem.objects.create(order=self.order, product=self.product, colour=self.colour,
                                              size=self.size, quantity=2)
        order_item.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse('cart:decrease-quantity', kwargs={'pk': order_item.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cart:summary'))
        updated_order_item = get_object_or_404(OrderItem, pk=order_item.pk)
        self.assertEqual(updated_order_item.quantity, order_item.quantity - 1)

    def test_delete_item_when_its_quantity_is_0(self):
        order_item = OrderItem.objects.create(order=self.order, product=self.product, colour=self.colour,
                                              size=self.size, quantity=1)
        order_item.save()
        self.client.force_login(self.user)
        initial_order_item_count = OrderItem.objects.count()
        response = self.client.get(reverse('cart:decrease-quantity', kwargs={'pk': order_item.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cart:summary'))
        updated_order_item_count = OrderItem.objects.count()
        self.assertEqual(updated_order_item_count, initial_order_item_count - 1)


class RemoveFromCartViewTest(TestCase):
    dummy_image = SimpleUploadedFile(
        name='test_image.jpg',
        content=open('media/test_image.jpg', 'rb').read(),
        content_type='image/jpeg'
    )

    def test_valid_url(self):
        response = self.client.get(reverse('cart:remove-from-cart', kwargs={'pk': self.order_item.pk}))
        self.assertEqual(response.status_code, 302)

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.category = Category.objects.create(name='Test Category')
        self.colour = ColourVariation.objects.create(name='red')
        self.size = SizeVariation.objects.create(name='M')
        self.order = Order(user=self.user)
        self.order.save()
        self.product = Product.objects.create(title='Product 1', slug='product-1', image=self.dummy_image,
                                              primary_category=self.category, price=100, stock=10)
        self.order_item = OrderItem.objects.create(order=self.order, product=self.product, colour=self.colour,
                                                   size=self.size, quantity=2)

    def test_remove_from_cart_view(self):
        order_item = OrderItem.objects.create(order=self.order, product=self.product, colour=self.colour,
                                              size=self.size, quantity=2)
        order_item.save()
        initial_order_item_count = OrderItem.objects.count()
        response = self.client.get(reverse('cart:remove-from-cart', kwargs={'pk': order_item.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cart:summary'))
        updated_order_item_count = OrderItem.objects.count()
        self.assertEqual(updated_order_item_count, initial_order_item_count - 1)


class CheckoutViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_login(self.user)
        self.address_data = {
            'Adres_zamieszkania1': 'Test Address 1',
            'Adres_zamieszkania2': 'Test Address 2',
            'shipping_zip_code': '12345',
            'shipping_city': 'Test City',
            'billing_address_line1': 'Test Billing Address 1',
            'billing_address_line2': 'Test Billing Address 2',
            'billing_zip_code': '67890',
            'billing_city': 'Test Billing City',
        }

    def test_correct_url_and_template(self):
        response = self.client.get(reverse('cart:checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart/checkout.html')

    def test_checkout_view_with_existing_shipping_address(self):
        shipping_address = Address.objects.create(
            user=self.user,
            address_line_1='Shipping Address 1',
            address_line_2='Shipping Address 2',
            zip_code='11111',
            city='Existing City',
            address_type='S',
        )

        self.client.force_login(self.user)
        form_data = self.address_data.copy()
        form_data['selected_shipping_address'] = shipping_address.pk
        response = self.client.post(reverse('cart:checkout'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:payment'))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.shipping_address, shipping_address)

    def test_checkout_view_with_new_shipping_address(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('cart:checkout'), data=self.address_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:payment'))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.shipping_address.address_line_1, self.address_data['Adres_zamieszkania1'])
        self.assertEqual(order.shipping_address.address_line_2, self.address_data['Adres_zamieszkania2'])
        self.assertEqual(order.shipping_address.zip_code, self.address_data['shipping_zip_code'])
        self.assertEqual(order.shipping_address.city, self.address_data['shipping_city'])

    def test_checkout_view_with_existing_billing_address(self):
        billing_address = Address.objects.create(
            user=self.user,
            address_line_1='Billing Address 1',
            address_line_2='Billing Address 2',
            zip_code='99999',
            city='Existing Billing City',
            address_type='B',
        )

        self.client.force_login(self.user)
        form_data = self.address_data.copy()
        form_data['selected_billing_address'] = billing_address.pk
        response = self.client.post(reverse('cart:checkout'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:payment'))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.billing_address, billing_address)

    def test_checkout_view_with_new_billing_address(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('cart:checkout'), data=self.address_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cart:payment'))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.billing_address.address_line_1, self.address_data['billing_address_line1'])
        self.assertEqual(order.billing_address.address_line_2, self.address_data['billing_address_line2'])
        self.assertEqual(order.billing_address.zip_code, self.address_data['billing_zip_code'])
        self.assertEqual(order.billing_address.city, self.address_data['billing_city'])

    def test_checkout_view_with_invalid_form_data(self):
        self.client.force_login(self.user)
        form_data = {}
        response = self.client.post(reverse('cart:checkout'), data=form_data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)


class PaymentViewTest(TestCase):

    def test_view_accessible_template(self):
        response = self.client.get(reverse('cart:payment'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart/payment.html')


class ConfirmOrderViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('cart:confirm-order')

    def test_confirm_order_success(self):
        payment_data = {
            "purchase_units": [
                {
                    "amount": {
                        "value": "100.00"
                    }
                }
            ]
        }

        response = self.client.post(self.url, data=json.dumps(payment_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"data": "Success"})
        order = Order.objects.get(id=self.client.session.get('order_id'))
        payment = Payment.objects.get(order=order)
        self.assertTrue(payment.successful)
        self.assertEqual(payment.amount, 100.00)
        self.assertEqual(payment.payment_method, 'paypal')
        self.assertEqual(payment.raw_response, json.dumps(payment_data))
        order.refresh_from_db()
        self.assertTrue(order.ordered)
        self.assertIsNotNone(order.ordered_date)
        reference_number_expected = f"PAYMENT-{order}-{payment.id}"
        self.assertEqual(payment.reference_number, reference_number_expected)


class ThankYouViewTest(TestCase):

    def test_use_correct_template_and_url(self):
        response = self.client.get(reverse('cart:thank-you'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('cart/thank-you.html')


class OrderDetailViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.order = Order(user=self.user)
        self.order.save()
        self.url = reverse('cart:order-detail', kwargs={'pk': self.order.pk})

    def test_order_detail_view_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_order_detail_view_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart/order.html')
        self.assertEqual(response.context['order'], self.order)


class DeliveryViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.delivery = Delivery.objects.create(type='Standard', cost=500)
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_login(self.user)

    def test_delivery_view(self):
        response = self.client.get(reverse('cart:delivery'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart/delivery.html')
        self.assertTrue('form' in response.context)

    def test_delivery_form_valid(self):
        form_data = {'delivery': self.delivery.id}
        print(form_data)
        response = self.client.post(reverse('cart:delivery'), data=form_data)
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(id=self.client.session.get('order_id'))
        self.assertEqual(order.delivery, self.delivery)

    def test_delivery_form_invalid(self):
        form_data = {}
        response = self.client.post(reverse('cart:delivery'), form_data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors)

    def test_delivery_model(self):
        delivery = Delivery.objects.create(type='Express', cost=1000)
        self.assertEqual(str(delivery), 'Express - 10.00 zł')
        self.assertEqual(delivery.get_total(), '10.00')
