from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    path('shop/', views.ProductListView.as_view(), name='product-list'),
    path('shop/<slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('', views.CartView.as_view(), name='summary'),
    path('increase_quantity/<pk>/', views.IncreaseQuantityView.as_view(), name='increase-quantity'),
    path('decrease_quantity/<pk>/', views.DecreaseQuantityView.as_view(), name='decrease-quantity'),
    path('remove-from-cart/<pk>/', views.RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('payment/', views.PaymentView.as_view(), name='payment'),
    path('thank-you/', views.ThankYouView.as_view(), name='thank-you'),
    path('confirm-order/', views.ConfirmOrderView.as_view(), name='confirm-order'),
    path('orders/<pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('delivery/', views.DeliveryView.as_view(), name='delivery'),

]
