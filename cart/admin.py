from django.contrib import admin

from . import models

admin.site.register(models.Product)
admin.site.register(models.Order)
admin.site.register(models.OrderItem)
admin.site.register(models.ColourVariation)
admin.site.register(models.SizeVariation)
admin.site.register(models.Delivery)
admin.site.register(models.Category)
