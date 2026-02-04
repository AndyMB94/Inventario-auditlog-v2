from audit.tracking import log_read_list, log_read_detail


class AuditReadMixin:
    """
    Mixin para ViewSets que registra operaciones de lectura (list, retrieve).

    Uso:
        class ProductViewSet(AuditReadMixin, viewsets.ModelViewSet):
            queryset = Product.objects.all()
            serializer_class = ProductSerializer
    """

    def list(self, request, *args, **kwargs):
        """Intercepta list() para registrar ACCESS (listado)"""
        response = super().list(request, *args, **kwargs)

        # Solo registrar si la peticion fue exitosa
        if response.status_code == 200:
            extra_data = {
                'ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'count': len(response.data.get('results', response.data)) if isinstance(response.data, dict) else len(response.data)
            }

            log_read_list(
                user=request.user if request.user.is_authenticated else None,
                model_class=self.queryset.model,
                extra_data=extra_data
            )

        return response

    def retrieve(self, request, *args, **kwargs):
        """Intercepta retrieve() para registrar ACCESS (detalle)"""
        response = super().retrieve(request, *args, **kwargs)

        # Solo registrar si la peticion fue exitosa
        if response.status_code == 200:
            instance = self.get_object()
            extra_data = {
                'ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }

            log_read_detail(
                user=request.user if request.user.is_authenticated else None,
                instance=instance,
                extra_data=extra_data
            )

        return response

    def _get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
