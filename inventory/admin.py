from django.contrib import admin
from .models import Product, Category, Supplier


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'stock')
    list_filter = ('category',)
    search_fields = ('name',)
    filter_horizontal = ('suppliers',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'contact_person')
    search_fields = ('name', 'email', 'contact_person')