from django.http import JsonResponse
from django.templatetags.static import static
import json
import phonenumbers

from .models import Product, Order, OrderItem
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


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


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(max_length=100, allow_blank=False)
    lastname = serializers.CharField(max_length=100, allow_blank=False)
    phonenumber = serializers.CharField(max_length=20, allow_blank=False)
    address = serializers.CharField(max_length=200, allow_blank=False)

    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 
            'firstname', 
            'lastname', 
            'phonenumber', 
            'address', 
            'products'
        ]


    def validate_products(self, value):
        product_ids = [item['product'].id for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError('Нельзя добавлять один и тот же товар дважды.')
        return value


    def validate_phonenumber(self, value):
        try:
            parsed = phonenumbers.parse(value, 'RU')
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError('Введен неверный номер телефона')
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError('Введен неверный номер телефона')
        return value


    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        for item in products_data:
            OrderItem.objects.create(
                order=order, 
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price,
            )
        return order


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=200)