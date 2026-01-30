from rest_framework import serializers
from .models import Category, Product, Supplier


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    suppliers_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'category_name', 'price', 'stock', 'suppliers', 'suppliers_detail']

    def get_suppliers_detail(self, obj):
        return [{'id': s.id, 'name': s.name} for s in obj.suppliers.all()]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'