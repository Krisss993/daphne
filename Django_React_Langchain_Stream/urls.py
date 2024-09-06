"""
URL configuration for Django_React_Langchain_Stream project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
import core.views as views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/',include('langchain_stream.urls')),
    path('convs/',include('langchain_chat.urls')),
    path('accounts/', include('allauth.urls')),
    path('', views.HomeView.as_view(), name='home'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('cart/', include('cart.urls', namespace='cart')),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('accounts/', include('allauth.urls')),
    path('staff/', include('staff.urls', namespace='staff')),
    path('ml/', include('ml.urls', namespace='ml')),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


