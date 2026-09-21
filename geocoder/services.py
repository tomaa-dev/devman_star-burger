import requests
from django.conf import settings
from geocoder.models import Location


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return float(lat), float(lon)
    except (requests.exceptions.RequestException, KeyError, ValueError, IndexError):
        return None


def get_coords(address, coords_cache=None):
    if coords_cache is None:
        coords_cache = {}

    if address in coords_cache:
        return coords_cache[address]

    cached = Location.objects.filter(address=address).first()
    if cached:
        coords_cache[address] = (cached.lat, cached.lon)
        return coords_cache[address]

    coords = fetch_coordinates(settings.YANDEX_GEOCODER_API_KEY, address)
    if coords is None:
        coords_cache[address] = None
        return None

    lat, lon = coords
    Location.objects.get_or_create(
        address=address,
        defaults={'lat': lat, 'lon': lon},
    )
    coords_cache[address] = coords
    return coords
