import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from preference_app.models import SurveyQuestion, PreferenceResult

User = get_user_model()
c = Client()

# Create a test user
User.objects.filter(email='test_jewelry@example.com').delete()
user = User.objects.create_user(email='test_jewelry@example.com', name='Test Jewelry', password='password')

# Login
c.login(username='test_jewelry@example.com', password='password')

# Simulate answers
likert_answers = {
    "Style": [5, 4, 3],
    "Material": [4, 5, 2],
    "Occasion": [5, 4, 3],
    "Aesthetic": [5, 5, 5],
    "Budget": [3, 2, 4],
}

open_texts = [
    "I love wearing bold, vintage gold jewelry that makes me stand out at parties.",
    "Geometric patterns and unique aesthetics really appeal to me."
]

payload = {
    "likert_answers": likert_answers,
    "open_texts": open_texts
}

response = c.post('/survey/submit/', json.dumps(payload), content_type='application/json')
print(f"Submit Response Status: {response.status_code}")
try:
    print(f"Submit JSON: {response.json()}")
except Exception as e:
    print(e)
    print(response.content.decode())

# Print preference result
try:
    result = PreferenceResult.objects.get(user=user)
    print("\nDatabase Result:")
    print(f"Style: {result.style_score}")
    print(f"Material: {result.material_score}")
    print(f"Occasion: {result.occasion_score}")
    print(f"Aesthetic: {result.aesthetic_score}")
    print(f"Budget: {result.budget_score}")
    print(f"Persona: {result.jewelry_persona}")
    print(f"Recommendations: {result.recommendations}")
except Exception as e:
    print("\nFailed to get result from DB:")
    print(e)
