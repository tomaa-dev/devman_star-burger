from django.http import JsonResponse
from django.templatetags.static import static
import json

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


@api_view(['GET', 'POST'])
def register_order(request):
    if request.method == 'GET':
        orders = Order.objects.all().prefetch_related('items__product')
        dumped_orders = []
        for order in orders:
            dumped_orders.append({
                'id': order.id,
                'firstname': order.firstname,
                'lastname': order.lastname,
                'phonenumber': str(order.phonenumber),
                'address': order.address,
                'products': [
                    {
                        'product': item.product.name,
                        'quantity': item.quantity,
                    } for item in order.items.all()
                ]
            })
        return Response(dumped_orders)

    try:
        order_data = json.loads(request.body.decode())
        print("Данные заказа:", order_data)
        
        order = Order.objects.create(
            firstname=order_data['firstname'],
            lastname=order_data['lastname'],
            phonenumber=order_data['phonenumber'],
            address=order_data['address'],
        )
        
        for product_data in order_data['products']:
            product = Product.objects.get(id=product_data['product'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=product_data['quantity'],
            )
        return JsonResponse({'status': 'ok'}, status=201)
    except ValueError:
        return JsonResponse({
            'error': 'Некорректный JSON',
        }, status=400)

