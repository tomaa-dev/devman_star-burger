import sys

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from foodcartapp.models import Product, ProductCategory


class Command(BaseCommand):
    help = 'Загружает данные из json-файла'


    def add_arguments(self, parser):
        parser.add_argument('json_url', type=str)


    def handle(self, *args, **options):
        json_url = options['json_url']
        try:
            response = requests.get(json_url)
            response.raise_for_status()
            burger_data = response.json()

        except requests.RequestException as e:
            self.stderr.write('Ошибка при загрузке json-файла')
            sys.exit(1)

        for burger in burger_data:
            burger_title = burger.get('title')
            self.stdout.write(f'Обрабатываю: {burger_title}')
            burger_category = burger.get('type')
            burger_price = burger.get('price')
            burger_img = burger.get('img', '')
            burger_description = burger.get('description', '')

            category_obj, _ = ProductCategory.objects.get_or_create(
                name=burger_category
            )

            burger, created = Product.objects.get_or_create(
                name=burger_title,
                defaults={
                    'category': category_obj,
                    'price': burger_price,
                    'description': burger_description,
                }
            )

            if created:
                img_url = f'https://raw.githubusercontent.com/devmanorg/star-burger-products/master/media/{burger_img}'
                img_response = requests.get(img_url)
                img_response.raise_for_status()

                burger.image.save(burger_img, ContentFile(img_response.content))

                self.stdout.write('Бургер успешно создан')
            else:
                self.stdout.write('Такой уже есть в базе')

