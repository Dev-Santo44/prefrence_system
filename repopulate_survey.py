import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preference_site.settings')
django.setup()

from preference_app.models import SurveyQuestion

def repopulate_questions():
    # Clear old questions
    SurveyQuestion.objects.all().delete()

    # Create new simplified personality-centric questions
    # Format: (Category, Question Text)
    # Categories: Style, Material, Occasion, Aesthetic, Budget
    questions = [
        ("Style", "I love being the center of attention in any room."),
        ("Style", "I feel more comfortable in simple, classic outfits."),
        ("Aesthetic", "I am always looking for something new and different."),
        ("Aesthetic", "I appreciate the heritage and history behind a product."),
        ("Material", "I value quality and precision in everything I own."),
        ("Material", "I like my accessories to have a soft and delicate look."),
        ("Occasion", "I often buy things to celebrate special milestones in my life."),
        ("Occasion", "I enjoy changing my look frequently to match my mood."),
        ("Budget", "I am willing to invest in luxury items that last a lifetime."),
        ("Budget", "I prefer finding great value and trendy pieces at a fair price."),
    ]

    for cat, text in questions:
        SurveyQuestion.objects.create(category=cat, question_text=text)

    print(f"Successfully added {len(questions)} simplified survey questions.")

if __name__ == "__main__":
    repopulate_questions()
