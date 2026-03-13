import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import SurveyQuestion

# Clear old questions
SurveyQuestion.objects.all().delete()

# Create new jewelry questions
questions = [
    # Style
    ("Style", "I prefer bold, statement-making jewelry over delicate, minimalist pieces."),
    ("Style", "I enjoy wearing unique, unconventional designs that stand out."),
    ("Style", "I lean towards timeless, classic styles rather than fast-fashion trends."),
    # Material
    ("Material", "The type of metal (e.g., solid gold, platinum) is very important to me."),
    ("Material", "I prefer jewelry with prominent gemstones or diamonds over plain metal."),
    ("Material", "I don't mind wearing high-quality alternative alloys instead of pure precious metals."),
    # Occasion
    ("Occasion", "I usually buy jewelry with a specific upscale event or party in mind."),
    ("Occasion", "I prefer versatile jewelry that I can wear every day, everywhere."),
    ("Occasion", "I only wear my best jewelry for formal or very special occasions."),
    # Aesthetic
    ("Aesthetic", "I strongly relate to a specific aesthetic (e.g., vintage, boho, or gothic) in my accessorizing."),
    ("Aesthetic", "I like my jewelry to look modern and sleek rather than ornate and traditional."),
    ("Aesthetic", "I enjoy mixing different vibes and themes depending on my mood."),
    # Budget
    ("Budget", "I consider jewelry an investment and am willing to pay a premium for high-end designer pieces."),
    ("Budget", "I prefer to buy affordable fashion jewelry so I can have a larger variety."),
    ("Budget", "I look for the best value and prioritize craftsmanship over brand names."),
]

for cat, text in questions:
    SurveyQuestion.objects.create(category=cat, question_text=text)

print(f"Added {len(questions)} jewelry survey questions.")
