import os
import sys
import django
import pandas as pd
from django.db.models import Count, Avg, F
from django.utils import timezone
from datetime import timedelta

# Bootstrap Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "preference_site.settings")
django.setup()

from preference_app.models import PreferenceResult, JewelryCatalog, User, SwipeResponse

def get_total_stats():
    """Returns basic counts for the dashboard tiles."""
    return {
        "total_users": User.objects.count(),
        "total_recommendations": PreferenceResult.objects.count(),
        "total_catalog_items": JewelryCatalog.objects.count(),
        "total_swipes": SwipeResponse.objects.count()
    }

def get_persona_distribution():
    """Returns a DataFrame of persona counts."""
    data = (
        PreferenceResult.objects.values("jewelry_persona")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return pd.DataFrame(list(data))

def get_budget_by_style():
    """Returns average budget score grouped by style score brackets or persona."""
    data = (
        PreferenceResult.objects.values("jewelry_persona")
        .annotate(avg_budget=Avg("budget_score"), avg_style=Avg("style_score"))
        .order_by("jewelry_persona")
    )
    return pd.DataFrame(list(data))

def get_weekly_signups():
    """Returns user registration counts for the last 8 weeks."""
    today = timezone.now()
    eight_weeks_ago = today - timedelta(weeks=8)
    
    users = User.objects.filter(date_joined__gte=eight_weeks_ago).values("date_joined")
    df["date"] = pd.to_datetime(df["date_joined"]).dt.date
    
    if df.empty:
        return pd.DataFrame(columns=["date", "count"])
    
    df["date"] = pd.to_datetime(df["created_at"]).dt.date
    df = df.groupby("date").size().reset_index(name="count")
    return df

def get_dimension_averages():
    """Returns the average score across all 5 jewelry dimensions."""
    avg = PreferenceResult.objects.aggregate(
        Style=Avg("style_score"),
        Material=Avg("material_score"),
        Occasion=Avg("occasion_score"),
        Aesthetic=Avg("aesthetic_score"),
        Budget=Avg("budget_score")
    )
    # Convert dict to DataFrame for radar chart
    df = pd.DataFrame([
        {"Dimension": k, "Score": v or 0} for k, v in avg.items()
    ])
    return df

def get_top_catalog_items():
    """Returns the most liked items from swipe responses."""
    data = (
        SwipeResponse.objects.filter(action="like")
        .values("catalog_item__name", "catalog_item__item_type")
        .annotate(likes=Count("id"))
        .order_by("-likes")[:10]
    )
    return pd.DataFrame(list(data))

def search_user_profile(email):
    """Finds a user's preference result by email."""
    try:
        res = PreferenceResult.objects.get(user__email__iexact=email)
        return res.as_dict()
    except PreferenceResult.DoesNotExist:
        return None
