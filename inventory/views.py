from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import HttpResponse
from .models import Category, Product, Supplier, Customer
from .serializers import CategorySerializer, ProductSerializer, SupplierSerializer, CustomerSerializer
from audit.mixins import AuditReadMixin
from audit.tracking import log_export
from openpyxl import Workbook
from datetime import datetime


class CategoryViewSet(AuditReadMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'message': 'Categoría creada exitosamente',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'message': 'Categoría actualizada exitosamente',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Categoría eliminada exitosamente'
        }, status=status.HTTP_200_OK)


class ProductViewSet(AuditReadMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'message': 'Producto creado exitosamente',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'message': 'Producto actualizado exitosamente',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Producto eliminado exitosamente'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='export')
    def export_to_excel(self, request):
        """Exporta todos los productos a Excel y registra la acción en auditlog"""
        # Obtener productos
        products = self.get_queryset()

        # Crear workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Productos"

        # Headers
        headers = ['ID', 'Nombre', 'Categoría', 'Precio', 'Stock', 'Proveedores']
        ws.append(headers)

        # Datos
        for product in products:
            suppliers = ', '.join([s.name for s in product.suppliers.all()])
            ws.append([
                product.id,
                product.name,
                product.category.name if product.category else '',
                float(product.price),
                product.stock,
                suppliers
            ])

        # Registrar en auditlog
        log_export(
            user=request.user if request.user.is_authenticated else None,
            model_class=Product,
            export_format='excel',
            extra_data={
                'count': products.count(),
                'ip': self._get_client_ip(request)
            }
        )

        # Preparar respuesta
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'productos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'

        wb.save(response)
        return response


class SupplierViewSet(AuditReadMixin, viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'message': 'Proveedor creado exitosamente',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'message': 'Proveedor actualizado exitosamente',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Proveedor eliminado exitosamente'
        }, status=status.HTTP_200_OK)


class CustomerViewSet(AuditReadMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'message': 'Cliente creado exitosamente',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'message': 'Cliente actualizado exitosamente',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Cliente eliminado exitosamente'
        }, status=status.HTTP_200_OK)