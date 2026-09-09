from django.http import JsonResponse
from django.templatetags.static import static
import json
import phonenumbers

from .models import Product, Order, OrderItem
from rest_framework.decorators import api_view
from rest_framework.response import Response


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    try:
        order_data = json.loads(request.body.decode())
        print("Данные заказа:", order_data)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)

    fields = ['firstname', 'lastname', 'phonenumber', 'address']
    for field in fields:
        if field not in order_data:
            return JsonResponse({field: 'Обязательное поле.'}, status=400)
        value = order_data[field]
        if value is None:
            return JsonResponse({field: 'Это поле не может быть пустым.'}, status=400)
        if not isinstance(value, str):
            return JsonResponse({field: 'Not a valid string.'}, status=400)
        if not value.strip():
            return JsonResponse({field: 'Это поле не может быть пустым.'}, status=400)

    if 'products' not in order_data:
        return JsonResponse({'products': 'Обязательное поле.'}, status=400)
    if not phonenumbers.is_valid_number(phonenumbers.parse(order['phonenumber'])):
        return Response(['введен неверный номер телефона'], status=200)

    products_data = order_data['products']
    if not isinstance(products_data, list):
        return JsonResponse({'products': 'Ожидался list со значениями, но был получен "str"'}, status=400)

    if not products_data:
        return JsonResponse({'products': 'Это поле не может быть пустым.'}, status=400)

    order = Order.objects.create(
        firstname=order_data['firstname'],
        lastname=order_data['lastname'],
        phonenumber=order_data['phonenumber'],
        address=order_data['address'],
    )

    for product_data in products_data:
        if 'product' not in product_data or product_data['product'] is None:
            return JsonResponse({'products': 'Поле обязательно и не может быть пустым.'}, status=400)
        product_id = product_data['product']
        if not isinstance(product_id, int):
            return JsonResponse({'products': 'Поле должно быть целым числом'}, status=400)

        try:
            product = Product.objects.get(id=product_data['product'])
        except Product.DoesNotExist:
            return JsonResponse(
                {'products': 'Заказ с несуществующим id продукта'}, 
                status=400
            )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=product_data['quantity'],
        )
    return JsonResponse({'status': 'ok'}, status=201)