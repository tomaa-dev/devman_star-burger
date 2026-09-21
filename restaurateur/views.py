from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from geopy.distance import distance

from foodcartapp.models import (Order, OrderItem, Product, Restaurant,
                                RestaurantMenuItem)

from geocoder.models import Location
from geocoder.services import get_coords


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = (
        Order.objects
        .with_total_cost()
        .prefetch_related('items__product')
        .select_related('restaurant')
        .order_by('status', 'id')
    )

    menu_items = (
        RestaurantMenuItem.objects
        .filter(availability=True)
        .select_related('restaurant')
    )

    product_to_restaurants = {}
    restaurants_by_id = {}
    for item in menu_items:
        product_to_restaurants.setdefault(item.product_id, set()).add(item.restaurant_id)
        restaurants_by_id[item.restaurant_id] = item.restaurant

    all_addresses = {order.address for order in orders}
    all_addresses |= {restaurant.address for restaurant in restaurants_by_id.values()}

    coords_cache = {
        loc.address: (loc.lat, loc.lon)
        for loc in Location.objects.filter(address__in=all_addresses)
    }

    for order in orders:
        product_ids = [item.product_id for item in order.items.all()]
        if product_ids:
            candidates = set(restaurants_by_id.keys())
            for product_id in product_ids:
                candidates &= product_to_restaurants.get(product_id, set())
            restaurants_list = [restaurants_by_id[rid] for rid in candidates]
            client_coords = get_coords(order.address, coords_cache=coords_cache)

            items = []
            for restaurant in restaurants_list:
                rest_coords = get_coords(restaurant.address, coords_cache=coords_cache)
                dist_km = None
                if client_coords and rest_coords:
                    dist_km = distance(client_coords, rest_coords).km
                items.append((restaurant, dist_km))

            items.sort(key=lambda x: (x[1] is None, x[1] or 0))
            order.available_restaurants = items
        else:
            order.available_restaurants = []

    return render(request, 'order_items.html', context={
        'order_items': orders,
    })
    