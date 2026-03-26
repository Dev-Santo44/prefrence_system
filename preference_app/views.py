"""
Django Views for AI-Driven Personal Preference Identifier.
Handles: login, register, logout, survey, survey submit, dashboard.
"""

import sys
import os
import random
import json

import numpy as np

from .models import SwipeResponse, JewelryCatalog, PreferenceResult, SwipeSession

# Allow imports from project root (for models/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

from preference_app.forms import RegisterForm, LoginForm
from preference_app.models import (
    SurveyQuestion, Response, PreferenceResult, SwipeSession, 
    SwipeResponse, JewelryCatalog, ChatSession, ChatMessage, RecentlyViewed
)
from models.jewelry_scorer import score_and_recommend
from preference_app.chat_engine import get_chatbot_response
from preference_app.tryon_engine import process_tryon
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

User = get_user_model()


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_unique_products(queryset, limit=50):
    """Deduplicate queryset by image_url in memory for SQLite."""
    seen = set()
    unique = []
    for item in queryset:
        if item.image_url not in seen:
            unique.append(item)
            seen.add(item.image_url)
        if len(unique) >= limit:
            break
    return unique

# ── Landing / Auth ────────────────────────────────────────────────────────────

def index_view(request):
    """E-commerce style home page with recommendations."""
    
    # ── Trending Now (Newest/Random items) ──
    trending_qs = JewelryCatalog.objects.exclude(image_url="").order_by('-id')[:40]
    trending_items = get_unique_products(trending_qs, limit=8)

    # ── Recommended for You (Based on Personality) ──
    recommended_items = JewelryCatalog.objects.none()
    if request.user.is_authenticated:
        try:
            result = request.user.preference_result
            persona = result.jewelry_persona or ""
            
            # Advanced Persona-to-Catalog Mapping for high-end boutique feel
            persona_map = {
                "Minimalist Luxe":  {"style": "Minimalist", "material": "Gold"},
                "Bold Statement":   {"style": "Statement", "aesthetic": "Modern"},
                "Classic Elegance": {"aesthetic": "Traditional", "material": "Diamond"},
                "Bohemian Spirit":  {"aesthetic": "Vintage", "item_type": "Earring"},
                "Modern Artisan":   {"style": "Modern", "material": "Silver"}
            }
            
            p_filters = persona_map.get(persona, {})
            recommended_items = JewelryCatalog.objects.filter(**p_filters).exclude(image_url="").order_by('?')[:30]
            
            # Use deduplication helper
            recommended_items_list = get_unique_products(recommended_items, limit=4)
            
            # Fallback for empty results
            if not recommended_items_list:
                fallback = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:30]
                recommended_items_list = get_unique_products(fallback, limit=4)
                
            recommended_items = recommended_items_list
        except (PreferenceResult.DoesNotExist, Exception):
            fallback = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:30]
            recommended_items = get_unique_products(fallback, limit=4)

    # ── Recently Viewed ──
    recently_viewed = []
    if request.user.is_authenticated:
        recently_viewed = RecentlyViewed.objects.filter(user=request.user).select_related('item')[:4]

    login_form    = LoginForm()
    register_form = RegisterForm()
    active_tab    = "login" 

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "login":
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                email    = login_form.cleaned_data["email"].lower()
                password = login_form.cleaned_data["password"]
                user     = authenticate(request, username=email, password=password)
                if user is not None:
                    login(request, user)
                    return redirect("index")
                else:
                    messages.error(request, "Invalid email or password.")
            active_tab = "login"

        elif action == "register":
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                email = register_form.cleaned_data["email"].lower()
                try:
                    user = User.objects.create_user(
                        email    = email,
                        name     = register_form.cleaned_data["name"],
                        password = register_form.cleaned_data["password"],
                    )
                    login(request, user)
                    messages.success(request, f"Welcome, {user.name}! Your account has been created.")
                    return redirect("survey")
                except Exception as e:
                    messages.error(request, f"Database error: {str(e)}")
            active_tab = "register"

    return render(request, "preference_app/index.html", {
        "login_form":    login_form,
        "register_form": register_form,
        "active_tab":    active_tab,
        "trending_items": trending_items,
        "recommended_items": recommended_items,
        "recently_viewed": recently_viewed,
    })


def logout_view(request):
    logout(request)
    return redirect("index")


# ── Survey ────────────────────────────────────────────────────────────────────

@login_required
def survey_view(request):
    """Render the survey page with all questions as JSON."""
    questions = list(
        SurveyQuestion.objects.values("id", "question_text", "category")
        .order_by("category", "id")
    )
    return render(request, "preference_app/survey.html", {
        "questions_json": json.dumps(questions),
        "total":          len(questions),
    })


@login_required
@require_POST
def survey_submit_view(request):
    """Handle AJAX survey submission."""
    try:
        body           = json.loads(request.body)
        likert_answers = body.get("likert_answers", {})
        open_texts     = body.get("open_texts", [])
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "Invalid payload."}, status=400)

    user = request.user
    Response.objects.filter(user=user).delete()
    for trait, ratings in likert_answers.items():
        questions = SurveyQuestion.objects.filter(category=trait).order_by("id")
        for i, q in enumerate(questions):
            if i < len(ratings):
                Response.objects.create(user=user, question=q, answer=str(ratings[i]))

    result = score_and_recommend(likert_answers, open_texts or None)
    PreferenceResult.objects.update_or_create(
        user=user,
        defaults={
            "style_score":     result["style"],
            "material_score":  result["material"],
            "occasion_score":  result["occasion"],
            "aesthetic_score": result["aesthetic"],
            "budget_score":    result["budget"],
            "jewelry_persona": result["persona"],
            "recommendations": result["recommendations"],
        },
    )
    return JsonResponse({"ok": True, "results": result})


# ── Swipe Interface ─────────────────────────────────────────────────────────────

@login_required
def swipe_view(request):
    items = list(
        JewelryCatalog.objects
        .exclude(image_url__isnull=True)
        .exclude(image_url__exact='')
        .values('id', 'name', 'item_type', 'image_url', 'material', 'price_range')
    )
    random.shuffle(items)
    items = items[:20]
    return render(request, 'preference_app/swipe.html', {
        'items_json': json.dumps(items),
        'items':      items,
        'total':      len(items)
    })


@login_required
def submit_swipe(request):
    if request.method != 'POST':
        return redirect('swipe')
    try:
        swipe_data = json.loads(request.POST.get('swipe_data', '[]'))
        session = SwipeSession.objects.create(user=request.user)
        for entry in swipe_data:
            try:
                item = JewelryCatalog.objects.get(id=entry['item_id'])
                SwipeResponse.objects.create(session=session, item=item, action=entry['action'])
            except JewelryCatalog.DoesNotExist:
                continue
        return redirect('dashboard')
    except Exception:
        return redirect('swipe')


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard_view(request):
    try:
        result = request.user.preference_result
    except PreferenceResult.DoesNotExist:
        messages.warning(request, "You haven't taken the survey yet.")
        return redirect("survey")

    sidebar_items = [
        {"id": "analysis",        "label": "Analysis",          "icon": "📊"},
        {"id": "tryon",           "label": "Virtual Try-On",    "icon": "✨"},
        {"id": "wishlist",        "label": "Wishlist",          "icon": "♥"},
        {"id": "occasion",        "label": "Occasion Filter",   "icon": "🔍"},
        {"id": "style-profile",   "label": "Style Profile",     "icon": "👤"},
        {"id": "recommendations", "label": "AI Recommendations", "icon": "🎯"},
        {"id": "personalisation", "label": "Personalisation",   "icon": "🧬"},
    ]

    def get_trait_metadata(label, value):
        meta = {
            "Style": {
                "desc": "Expression Level",
                "high": "Bold & Expressive. You command attention.",
                "low": "Understated Elegance. You prefer subtle designs.",
                "mid": "Versatile Chic. You balance statement with essentials."
            },
            "Material": {
                "desc": "Quality Priority",
                "high": "Premium Connoisseur.",
                "low": "Creative Alchemist.",
                "mid": "Quality Conscious."
            },
            "Occasion": {
                "desc": "Usage Context",
                "high": "Intentional Stylist.",
                "low": "Seamless Versatility.",
                "mid": "Adaptive Wearer."
            },
            "Aesthetic": {
                "desc": "Visual Theme",
                "high": "Cultivated Theme.",
                "low": "Eclectic Collector.",
                "mid": "Modern Fusion."
            },
            "Budget": {
                "desc": "Value Focus",
                "high": "Investment Minded.",
                "low": "Accessibly Trendy.",
                "mid": "Value Finder."
            }
        }
        t = meta.get(label, {})
        insight = t.get("mid", "")
        if value > 65: insight = t.get("high", "")
        elif value < 35: insight = t.get("low", "")
        return t.get("desc", ""), insight

    traits = []
    trait_configs = [
        ("Style",     "#818cf8", "✨"),
        ("Material",  "#34d399", "💎"),
        ("Occasion",  "#fbbf24", "🎉"),
        ("Aesthetic", "#f472b6", "🎨"),
        ("Budget",    "#f87171", "💰"),
    ]
    
    for label, color, icon in trait_configs:
        val = getattr(result, f"{label.lower()}_score", 0)
        desc, insight = get_trait_metadata(label, val)
        traits.append({
            "label": label, "value": val, "color": color, 
            "icon": icon, "desc": desc, "insight": insight
        })

    persona = result.jewelry_persona or ""
    tryon_items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:12]

    from .models import Wishlist
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('item')
    occasions = JewelryCatalog.objects.values_list('occasion', flat=True).distinct()
    all_items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:40]
    feed_items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:15]

    return render(request, "preference_app/dashboard.html", {
        "result":             result,
        "result_json":        json.dumps(result.as_dict()),
        "sidebar_items":      sidebar_items,
        "traits":             traits,
        "tryon_items":        tryon_items,
        "wishlist_items":     wishlist_items,
        "ai_recommendations": tryon_items[:6], # Mocking
        "occasions":          occasions,
        "all_items":          all_items,
        "feed_items":         feed_items,
    })


@login_required
@require_POST
def wishlist_toggle(request):
    try:
        data = json.loads(request.body)
        item_id = data.get("item_id")
        from .models import Wishlist, JewelryCatalog
        item = JewelryCatalog.objects.get(id=item_id)
        wish, created = Wishlist.objects.get_or_create(user=request.user, item=item)
        if not created:
            wish.delete()
            return JsonResponse({"ok": True, "added": False})
        return JsonResponse({"ok": True, "added": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── Separate Pages ───────────────────────────────

@login_required
def look_builder_view(request):
    items = JewelryCatalog.objects.exclude(image_url="").order_by('item_type')
    categorized = {}
    for item in items:
        rtype = item.item_type or "Jewelry"
        if rtype not in categorized: categorized[rtype] = []
        categorized[rtype].append(item)
    return render(request, "preference_app/look_builder.html", {"title": "Look Builder", "categorized": categorized})

@login_required
def gallery_view(request):
    items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:15]
    posts = []
    users = ["@aura_jewelry", "@luxe_vibe", "@gold_standard", "@minimalist_me", "@bridal_glow"]
    for i, item in enumerate(items):
        posts.append({
            "user": users[i % len(users)], "image": item.image_url, 
            "product": item.name, "likes": (i + 1) * 42, "tag": item.occasion or "Daily Wear"
        })
    return render(request, "preference_app/gallery.html", {"title": "Community Gallery", "posts": posts})

@login_required
def fit_guide_view(request):
    return render(request, "preference_app/fit_guide.html", {"title": "Fit & Size Guide"})

@login_required
def gifting_view(request):
    questions = [
        {"id": "vibe", "text": "Vibe?", "options": ["Classic", "Bold", "Minimalist"]},
        {"id": "metal", "text": "Metal?", "options": ["Gold", "Rose Gold", "Silver"]},
        {"id": "occasion", "text": "Occasion?", "options": ["Anniversary", "Birthday", "Check"]}
    ]
    gift_items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:6]
    return render(request, "preference_app/gifting.html", {"title": "Gifting Tools", "questions": questions, "gift_items": gift_items})

@login_required
def post_purchase_view(request):
    orders = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:2]
    return render(request, "preference_app/post_purchase.html", {"title": "Post-Purchase Hub", "orders": orders})


@login_required
@require_POST
def save_style_profile(request):
    try:
        data = json.loads(request.body)
        result = request.user.preference_result
        result.metal_preference = data.get("metal", "")
        result.style_aesthetic  = data.get("aesthetic", "")
        result.stone_preference = data.get("stone", "")
        result.save()
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── Static Pages ───────────────────────────────

def about_view(request):
    return render(request, "preference_app/about.html")

def contact_view(request):
    return render(request, "preference_app/contact.html")


# ── Chat & Try-On ───────────────────────────────

@require_POST
def chat_api_view(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        session_id   = data.get("session_id")
        user = request.user if request.user.is_authenticated else None
        if not session_id:
            session = ChatSession.objects.create(user=user)
            session_id = session.id
        else:
            session = ChatSession.objects.filter(id=session_id).first()
            if not session: session = ChatSession.objects.create(user=user); session_id = session.id
            
        bot_reply, recommendations = get_chatbot_response(user, session_id, user_message)
        return JsonResponse({"session_id": session_id, "reply": bot_reply, "recommendations": recommendations})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def chat_history_view(request):
    session_id = request.GET.get("session_id")
    if not session_id: return JsonResponse({"messages": []})
    messages = ChatMessage.objects.filter(session_id=session_id).order_by("timestamp")
    serialized = [{"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in messages]
    return JsonResponse({"messages": serialized})

@login_required
@require_POST
def tryon_api_view(request):
    import tempfile
    try:
        user_photo = request.FILES.get("photo")
        item_id    = request.POST.get("item_id")
        item_type  = request.POST.get("item_type")
        if not user_photo: return JsonResponse({"error": "No photo"}, status=400)
        
        # 1. Save to local temporary file (OpenCV needs a real path)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            for chunk in user_photo.chunks():
                tmp.write(chunk)
            local_user_path = tmp.name

        # 2. Run try-on engine (saves result to local MEDIA_ROOT/tryon/)
        result_local_path = process_tryon(local_user_path, item_id, item_type)
        
        # Cleanup input temp file
        if os.path.exists(local_user_path):
            os.remove(local_user_path)

        if result_local_path and os.path.exists(result_local_path):
            # 3. Upload result to GCS
            filename = os.path.basename(result_local_path)
            with open(result_local_path, "rb") as f:
                gcs_path = default_storage.save(f"tryon/{filename}", ContentFile(f.read()))
            
            # Cleanup local result file
            os.remove(result_local_path)
            
            # 4. Return GCS URL
            return JsonResponse({"result_url": default_storage.url(gcs_path)})
            
        return JsonResponse({"error": "Processing failed"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def ar_tryon_view(request):
    """Render the real-time AR try-on page."""
    items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:20]
    return render(request, "preference_app/ar_tryon.html", {"tryon_items": items})



# ── Analysis ──

def compute_visual_preference_scores(user):
    liked_items = SwipeResponse.objects.filter(session__user=user, action='like').select_related('item')
    if not liked_items.exists(): return None
    vectors = [json.loads(r.item.visual_features) for r in liked_items if r.item.visual_features]
    if not vectors: return None
    avg_vector = np.mean(vectors, axis=0)
    chunk = len(avg_vector) // 5
    return {
        'style_score': float(np.mean(avg_vector[0:chunk])),
        'material_score': float(np.mean(avg_vector[chunk:chunk*2])),
        'occasion_score': float(np.mean(avg_vector[chunk*2:chunk*3])),
        'aesthetic_score': float(np.mean(avg_vector[chunk*3:chunk*4])),
        'budget_score': float(np.mean(avg_vector[chunk*4:]))
    }

@require_POST
def view_product_api(request, product_id):
    if not request.user.is_authenticated: return JsonResponse({"ok": False})
    try:
        item = JewelryCatalog.objects.get(id=product_id)
        RecentlyViewed.objects.update_or_create(user=request.user, item=item)
        return JsonResponse({"ok": True})
    except: return JsonResponse({"ok": False}, status=404)

def product_detail_api(request, product_id):
    """Fetch JSON details for the Quick View modal."""
    try:
        item = JewelryCatalog.objects.get(id=product_id)
        return JsonResponse({
            "id": item.id,
            "name": item.name,
            "price": str(item.price),
            "image": item.image_url,
            "description": "A stunning piece of luxury jewelry.",
            "type": item.item_type,
            "material": item.material,
            "style": item.style,
            "occasion": item.occasion,
        })
    except JewelryCatalog.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)


# ── Explore ──

def explore_view(request):
    """Catalog page with robust filtering for all items."""
    query = request.GET.get('q', '')
    itype = request.GET.get('type', '')
    material = request.GET.get('material', '')
    occasion = request.GET.get('occasion', '')
    sort = request.GET.get('sort', 'newest')

    items = JewelryCatalog.objects.all()

    if query:
        items = items.filter(Q(name__icontains=query) | Q(item_type__icontains=query))
    if itype:
        items = items.filter(item_type__iexact=itype)
    if material:
        items = items.filter(material__iexact=material)
    if occasion:
        items = items.filter(occasion__iexact=occasion)

    if sort == 'price_low':
        items = items.order_by('price')
    elif sort == 'price_high':
        items = items.order_by('-price')
    else:
        items = items.order_by('-id')

    types = JewelryCatalog.objects.values_list('item_type', flat=True).distinct()
    materials = JewelryCatalog.objects.values_list('material', flat=True).distinct()
    occasions = JewelryCatalog.objects.values_list('occasion', flat=True).distinct()

    context = {
        'items': get_unique_products(items, limit=60), 
        'types': sorted(filter(None, types)),
        'materials': sorted(filter(None, materials)),
        'occasions': sorted(filter(None, occasions)),
        'current_filters': {'q': query, 'type': itype, 'material': material, 'occasion': occasion, 'sort': sort}
    }
    return render(request, 'preference_app/explore.html', context)


# ── Trending Page ──

def trending_view(request):
    """Trending page showing live market rates, premium gold items, live news, and editorial blogs."""
    from preference_app.moneycontrol_service import get_live_metal_prices, get_jewelry_metal_news

    # ── Live Market Rates from MoneyControl ──
    live_prices = get_live_metal_prices()
    # Map to template-compatible format (backwards-compatible keys)
    market_rates = {}
    for key, data in live_prices.items():
        market_rates[key] = {
            "price": data.get("price", "0"),
            "trend": data.get("change", "+0.0%"),
            "direction": data.get("direction", "up"),
            "unit": data.get("unit", ""),
            "name": data.get("name", key),
        }

    # ── Live Jewelry/Metal News from MoneyControl ──
    live_news = get_jewelry_metal_news()

    # ── Fetch top premium items ──
    premium_gold_items = JewelryCatalog.objects.filter(
        Q(material__icontains='gold') | Q(price__gte=15000)
    ).order_by('-price')
    
    trending_gold_items = get_unique_products(premium_gold_items, limit=12)

    # ── Editorial Blogs (static fallback content) ──
    blogs = [
        {
            "title": "The Evolution of Minimalist Gold",
            "excerpt": "Discover how modern artisans are stripping back the layers to create breathtaking, understated pieces.",
            "image": f"https://storage.googleapis.com/{os.getenv('GS_BUCKET_NAME')}/products/ring/ring%2013.jpg",
            "date": "March 18, 2026",
            "read_time": "5 min read"
        },
        {
            "title": "Styling Tips for 2026: Layering Masterclass",
            "excerpt": "From delicate chains to statement pendants, learn the art of perfectly curated layering.",
            "image": f"https://storage.googleapis.com/{os.getenv('GS_BUCKET_NAME')}/products/necklace/necklace%205.jpg",
            "date": "March 15, 2026",
            "read_time": "4 min read"
        },
        {
            "title": "The Return of Vintage Glamour",
            "excerpt": "Why heavy, intricate traditional designs are making a massive comeback in bridal fashion.",
            "image": f"https://storage.googleapis.com/{os.getenv('GS_BUCKET_NAME')}/products/earrings/earrings%2047.jpg",
            "date": "March 10, 2026",
            "read_time": "7 min read"
        }
    ]

    context = {
        "market_rates": market_rates,
        "trending_items": trending_gold_items,
        "live_news": live_news,
        "blogs": blogs,
    }
    return render(request, 'preference_app/trending.html', context)
