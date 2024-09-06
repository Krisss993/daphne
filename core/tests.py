from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse

from cart.models import Order


class HomeViewTest(TestCase):
    def test_use_correct_template(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('index.html')


class ContactViewTest(TestCase):

    def test_use_correct_template(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('contact.html')

    def test_contact_form_valid(self):
        contact_data = {
            'imię': 'Testname',
            'email': 'test@email.com',
            'wiadomość': 'Test message'
        }

        response = self.client.post(reverse('contact'), data=contact_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(str(messages[0]), 'Dziękujemy za kontakt. Otrzymaliśmy wiadomość')

        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, 'Otrzymano wiadomość')
        self.assertEqual(sent_email.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(sent_email.to, [settings.NOTIFY_EMAIL])
        self.assertIn('Testname', sent_email.body)
        self.assertIn('test@email.com', sent_email.body)
        self.assertIn('Test message', sent_email.body)

    def test_contact_form_invalid(self):
        response = self.client.post(reverse('contact'), data={})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('contact.html')
        self.assertEqual(len(mail.outbox), 0)


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = Client()
        self.url = self.client.get(reverse('profile'))

    def test_context_update_with_orders(self):
        self.client.login(username='testuser', password='testpassword')
        order = Order.objects.create(user=self.user, ordered=True)
        url = reverse('profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertIn('orders', response.context)
        orders_in_context = response.context['orders']
        self.assertEqual(list(orders_in_context), [order])

    def test_context_update_without_orders(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertIn('orders', response.context)
        orders_in_context = response.context['orders']
        self.assertEqual(list(orders_in_context), [])
