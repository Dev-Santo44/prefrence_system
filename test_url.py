import os
import django
from django.urls import reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "preference_site.settings")
django.setup()

try:
    url = reverse('product_detail_page', args=[1])
    print(f"SUCCESS: reverse('product_detail_page', args=[1]) -> {url}")
except Exception as e:
    print(f"FAILED: reverse('product_detail_page', args=[1]) -> {e}")

try:
    url = reverse('product_detail_api', args=[1])
    print(f"SUCCESS: reverse('product_detail_api', args=[1]) -> {url}")
except Exception as e:
    print(f"FAILED: reverse('product_detail_api', args=[1]) -> {e}")
