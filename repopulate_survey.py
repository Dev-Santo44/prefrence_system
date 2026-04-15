import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import SurveyQuestion

def repopulate_questions():
    # Clear old questions
    SurveyQuestion.objects.all().delete()

    # New Personality-Centric Questions
    # Options are structured as a list of strings
    questions = [
        {
            "category": "Style",
            "text": "How would you describe your ideal evening out?",
            "options": [
                "An elegant gala or red-carpet event",
                "A cozy dinner with close friends",
                "An art gallery opening or indie concert",
                "A spontaneous adventure or road trip"
            ]
        },
        {
            "category": "Material",
            "text": "What draws you to a piece of jewelry first?",
            "options": [
                "The sparkle of rare gemstones",
                "The unique, handcrafted design",
                "How well it complements my daily outfit",
                "The bold statement it makes"
            ]
        },
        {
            "category": "Occasion",
            "text": "When choosing an outfit, what's your top priority?",
            "options": [
                "Timeless luxury and brand heritage",
                "Trendsetting and being fashionable",
                "Comfort and effortless chic",
                "Artistic expression and color"
            ]
        },
        {
            "category": "Aesthetic",
            "text": "How do others usually describe your personality?",
            "options": [
                "Sophisticated and poised",
                "Creative and quirky",
                "Practical and grounded",
                "Charismatic and bold"
            ]
        },
        {
            "category": "Budget",
            "text": "What’s your philosophy on investing in jewelry?",
            "options": [
                "Quality over quantity, always",
                "Versatility for every mood",
                "Sentimental value over market price",
                "Unique pieces that start conversations"
            ]
        }
    ]

    for q_data in questions:
        SurveyQuestion.objects.create(
            category=q_data["category"],
            question_text=q_data["text"],
            options=q_data["options"]
        )

    print(f"Successfully added {len(questions)} personality-centric survey questions.")

if __name__ == "__main__":
    repopulate_questions()
