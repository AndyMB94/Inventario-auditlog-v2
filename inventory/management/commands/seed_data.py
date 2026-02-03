from django.core.management.base import BaseCommand
from faker import Faker
from inventory.models import Category, Product, Customer, Supplier
import random


class Command(BaseCommand):
    help = 'Genera datos de prueba usando Faker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            type=int,
            default=0,
            help='Cantidad de categorias a crear (default: 0)'
        )
        parser.add_argument(
            '--suppliers',
            type=int,
            default=0,
            help='Cantidad de proveedores a crear (default: 0)'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=0,
            help='Cantidad de productos a crear (default: 0)'
        )
        parser.add_argument(
            '--customers',
            type=int,
            default=0,
            help='Cantidad de clientes a crear (default: 0)'
        )

    def handle(self, *args, **options):
        fake = Faker('es_ES')

        categories_count = options['categories']
        suppliers_count = options['suppliers']
        products_count = options['products']
        customers_count = options['customers']

        # Verificar que se pidio al menos un modelo
        if not any([categories_count, suppliers_count, products_count, customers_count]):
            self.stdout.write(self.style.WARNING(
                'No se especifico cantidad. Usa: --categories=N --suppliers=N --products=N --customers=N'
            ))
            return

        # Crear categorias
        if categories_count > 0:
            for i in range(categories_count):
                Category.objects.create(name=fake.word().capitalize())
                if (i + 1) % 50 == 0:
                    self.stdout.write(f'Categorias creadas: {i + 1}/{categories_count}')
            self.stdout.write(self.style.SUCCESS(f'Total categorias creadas: {categories_count}'))

        # Crear proveedores
        if suppliers_count > 0:
            for i in range(suppliers_count):
                Supplier.objects.create(
                    name=fake.company(),
                    email=fake.company_email(),
                    phone=fake.phone_number()[:20],
                    address=fake.address(),
                    contact_person=fake.name()
                )
                if (i + 1) % 50 == 0:
                    self.stdout.write(f'Proveedores creados: {i + 1}/{suppliers_count}')
            self.stdout.write(self.style.SUCCESS(f'Total proveedores creados: {suppliers_count}'))

        # Crear productos (requiere categorias existentes)
        if products_count > 0:
            categories = list(Category.objects.all())
            if not categories:
                self.stdout.write(self.style.ERROR(
                    'No hay categorias. Crea primero con --categories=N'
                ))
            else:
                suppliers = list(Supplier.objects.all())
                for i in range(products_count):
                    product = Product.objects.create(
                        name=fake.word().capitalize() + ' ' + fake.word(),
                        category=random.choice(categories),
                        price=round(random.uniform(10, 1000), 2),
                        stock=random.randint(0, 500)
                    )
                    # Asignar 0-3 proveedores aleatorios si existen
                    if suppliers:
                        num_suppliers = random.randint(0, min(3, len(suppliers)))
                        if num_suppliers > 0:
                            product.suppliers.set(random.sample(suppliers, num_suppliers))

                    if (i + 1) % 50 == 0:
                        self.stdout.write(f'Productos creados: {i + 1}/{products_count}')
                self.stdout.write(self.style.SUCCESS(f'Total productos creados: {products_count}'))

        # Crear clientes
        if customers_count > 0:
            for i in range(customers_count):
                Customer.objects.create(
                    name=fake.name(),
                    email=fake.email(),
                    phone=fake.phone_number()[:20],
                    address=fake.address()
                )
                if (i + 1) % 50 == 0:
                    self.stdout.write(f'Clientes creados: {i + 1}/{customers_count}')
            self.stdout.write(self.style.SUCCESS(f'Total clientes creados: {customers_count}'))
