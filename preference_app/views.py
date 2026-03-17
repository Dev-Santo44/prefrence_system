"""
Django Views for AI-Driven Personal Preference Identifier.
Handles: login, register, logout, survey, survey submit, dashboard.
"""

import sys
import os
import random
import json

import numpy as np


from .models import SwipeResponse, JewelryCatalog, PreferenceResult,SwipeSession

# Allow imports from project root (for models/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from preference_app.forms import RegisterForm, LoginForm
from preference_app.models import SurveyQuestion, Response, PreferenceResult, SwipeSession, SwipeResponse, JewelryCatalog, ChatSession, ChatMessage
from models.jewelry_scorer import score_and_recommend
from preference_app.chat_engine import get_chatbot_response
from preference_app.tryon_engine import process_tryon
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

User = get_user_model()


# ── Landing / Auth ────────────────────────────────────────────────────────────

def index_view(request):
    """Landing page with login & register tabs."""

    login_form    = LoginForm()
    register_form = RegisterForm()
    active_tab    = "login"  # default tab

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
                    return redirect("survey")
                else:
                    messages.error(request, "Invalid email or password.")
            active_tab = "login"

        elif action == "register":
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                user = User.objects.create_user(
                    email    = register_form.cleaned_data["email"].lower(),
                    name     = register_form.cleaned_data["name"],
                    password = register_form.cleaned_data["password"],
                )
                login(request, user)
                messages.success(request, f"Welcome, {user.name}! Your account has been created.")
                return redirect("survey")
            active_tab = "register"

    return render(request, "preference_app/index.html", {
        "login_form":    login_form,
        "register_form": register_form,
        "active_tab":    active_tab,
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
    """
    Handle AJAX survey submission.
    Expects JSON body: { likert_answers: {...}, open_texts: [...] }
    """
    try:
        body           = json.loads(request.body)
        likert_answers = body.get("likert_answers", {})
        open_texts     = body.get("open_texts", [])
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "Invalid payload."}, status=400)

    user = request.user

    # Save Likert responses
    Response.objects.filter(user=user).delete()  # clear old responses
    for trait, ratings in likert_answers.items():
        questions = SurveyQuestion.objects.filter(category=trait).order_by("id")
        for i, q in enumerate(questions):
            if i < len(ratings):
                Response.objects.create(user=user, question=q, answer=str(ratings[i]))

    # Compute OCEAN scores
    result = score_and_recommend(likert_answers, open_texts or None)

    # Save / update preference result
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


# FIXED version


@login_required
def swipe_view(request):
    # Get all catalog items that have an image URL
    items = list(
        JewelryCatalog.objects
        .exclude(image_url__isnull=True)
        .exclude(image_url__exact='')
        .values('id', 'name', 'item_type', 'image_url', 'material', 'price_range')
    )

    # Shuffle so each session feels fresh
    random.shuffle(items)

    # Limit to 20 items for the swipe session
    items = items[:20]

    return render(request, 'preference_app/swipe.html', {
        'items_json': json.dumps(items),   # for JavaScript
        'items':      items,               # for Django template
        'total':      len(items)
    })




@login_required
def submit_swipe(request):
    if request.method != 'POST':
        return redirect('swipe')

    try:
        swipe_data = json.loads(request.POST.get('swipe_data', '[]'))

        # Get or create a swipe session for this user
        session = SwipeSession.objects.create(user=request.user)

        # Save each swipe response
        for entry in swipe_data:
            try:
                item = JewelryCatalog.objects.get(id=entry['item_id'])
                SwipeResponse.objects.create(
                    session=session,
                    item=item,
                    action=entry['action']   # 'like' or 'dislike'
                )
            except JewelryCatalog.DoesNotExist:
                continue

        # Redirect to dashboard after swipe complete
        return redirect('dashboard')

    except Exception as e:
        return redirect('swipe')
# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard_view(request):
    try:
        result = request.user.preference_result
    except PreferenceResult.DoesNotExist:
        messages.warning(request, "You haven't taken the survey yet.")
        return redirect("survey")

    # ── Sidebar Items ──
    sidebar_items = [
        {"id": "analysis",        "label": "Analysis",          "icon": "📊"},
        {"id": "tryon",           "label": "Virtual Try-On",    "icon": "✨"},
        {"id": "wishlist",        "label": "Wishlist",          "icon": "♥"},
        {"id": "occasion",        "label": "Occasion Filter",   "icon": "🔍"},
        {"id": "style-profile",   "label": "Style Profile",     "icon": "👤"},
        {"id": "recommendations", "label": "AI Recommendations", "icon": "🎯"},
        {"id": "personalisation", "label": "Personalisation",   "icon": "🧬"},
    ]

    # ── Traits for Radar Chart / Detail ──
    def get_trait_metadata(label, value):
        meta = {
            "Style": {
                "desc": "Expression Level",
                "high": "Bold & Expressive. You gravitate towards pieces that command attention.",
                "low": "Understated Elegance. You prefer delicate, subtle designs.",
                "mid": "Versatile Chic. You balance statement pieces with daily essentials."
            },
            "Material": {
                "desc": "Quality Priority",
                "high": "Premium Connoisseur. You prioritize purity of metals and stones.",
                "low": "Creative Alchemist. You value the 'vibe' more than raw material value.",
                "mid": "Quality Conscious. You look for a balance of durability and design."
            },
            "Occasion": {
                "desc": "Usage Context",
                "high": "Intentional Stylist. Pieces are selected for specific life moments.",
                "low": "Seamless Versatility. You look for jewelry that works all day.",
                "mid": "Adaptive Wearer. You have a mix of daily and event-specific pieces."
            },
            "Aesthetic": {
                "desc": "Visual Theme",
                "high": "Cultivated Theme. Your collection follows a strong visual narrative.",
                "low": "Eclectic Collector. You enjoy mixing different visual eras.",
                "mid": "Modern Fusion. You appreciate classic roots with contemporary twists."
            },
            "Budget": {
                "desc": "Value Focus",
                "high": "Investment Minded. You favor legacy, designer, and custom pieces.",
                "low": "Accessibly Trendy. You enjoy rotating collections and fresh styles.",
                "mid": "Value Finder. You seek the best quality at a justifiable price point."
            }
        }
        t = meta.get(label, {})
        insight = t["mid"]
        if value > 65: insight = t["high"]
        elif value < 35: insight = t["low"]
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
            "label": label,
            "value": val,
            "color": color,
            "icon": icon,
            "desc": desc,
            "insight": insight
        })

    # ── Try-On & Recommendations ──
    persona = result.jewelry_persona or ""
    if "Bridal" in persona:
        tryon_items = JewelryCatalog.objects.filter(occasion="Bridal").exclude(image_url="")[:12]
    elif "Minimalist" in persona:
        tryon_items = JewelryCatalog.objects.filter(style="Minimalist").exclude(image_url="")[:12]
    else:
        tryon_items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:12]

    # AI Recs - combine persona with manual preferences
    style_pref = result.style_aesthetic or (persona.split()[-1] if persona else "Minimalist")
    material_pref = result.metal_preference or "Gold"
    
    ai_recommendations = JewelryCatalog.objects.filter(
        style__icontains=style_pref
    ).exclude(image_url="")
    
    if material_pref:
        ai_recommendations = ai_recommendations.filter(material__icontains=material_pref)
        
    ai_recommendations = ai_recommendations.order_by('?')[:10]
    
    if not ai_recommendations.exists():
        ai_recommendations = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:10]

    # ── Wishlist ──
    from .models import Wishlist
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('item')

    # ── Occasion Filter ──
    occasions = JewelryCatalog.objects.values_list('occasion', flat=True).distinct()
    all_items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:40]

    # ── Personalisation Feed ──
    feed_items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:15]

    return render(request, "preference_app/dashboard.html", {
        "result":             result,
        "result_json":        json.dumps(result.as_dict()),
        "sidebar_items":      sidebar_items,
        "traits":             traits,
        "tryon_items":        tryon_items,
        "wishlist_items":     wishlist_items,
        "ai_recommendations": ai_recommendations,
        "occasions":          occasions,
        "all_items":          all_items,
        "feed_items":         feed_items,
    })


@login_required
@require_POST
def wishlist_toggle(request):
    """AJAX view to add/remove item from wishlist."""
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


# ── Phase 2: Separate Pages ───────────────────────────────────────────────────

@login_required
def look_builder_view(request):
    items = JewelryCatalog.objects.exclude(image_url="").order_by('item_type')
    
    # Group items by type for the sidebar
    categorized = {}
    for item in items:
        rtype = item.item_type or "Jewelry"
        if rtype not in categorized:
            categorized[rtype] = []
        categorized[rtype].append(item)
        
    return render(request, "preference_app/look_builder.html", {
        "title": "Look Builder",
        "categorized": categorized
    })

@login_required
def gallery_view(request):
    # Simulated community posts using catalog items
    items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:15]
    posts = []
    users = ["@aura_jewelry", "@luxe_vibe", "@gold_standard", "@minimalist_me", "@bridal_glow"]
    
    for i, item in enumerate(items):
        posts.append({
            "user": users[i % len(users)],
            "image": item.image_url,
            "product": item.name,
            "likes": (i + 1) * 42,
            "tag": item.occasion or "Daily Wear"
        })
        
    return render(request, "preference_app/gallery.html", {
        "title": "Community Gallery",
        "posts": posts
    })

@login_required
def fit_guide_view(request):
    return render(request, "preference_app/fit_guide.html", {"title": "Fit & Size Guide"})

@login_required
def gifting_view(request):
    # Recipient style quiz questions
    questions = [
        {"id": "vibe", "text": "What's their overall vibe?", "options": ["Classic & Timeless", "Bold & Statement", "Minimalist & Subtle"]},
        {"id": "metal", "text": "Favorite metal color?", "options": ["Yellow Gold", "Rose Gold", "Silver/Platinum"]},
        {"id": "occasion", "text": "What's the occasion?", "options": ["Anniversary", "Birthday", "Just Because"]}
    ]
    
    # Pre-fetch some "giftable" items
    gift_items = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:6]
    
    return render(request, "preference_app/gifting.html", {
        "title": "Gifting Tools",
        "questions": questions,
        "gift_items": gift_items
    })

@login_required
def post_purchase_view(request):
    # Simulated orders from wishlist/catalog
    orders = JewelryCatalog.objects.exclude(image_url="").order_by('?')[:2]
    
    # Care guides
    care_guides = [
        {"id": "gold", "title": "Caring for Gold", "icon": "✨", "desc": "Keep your gold pieces sparkling with a soft cloth and warm water."},
        {"id": "gem", "title": "Gemstone Safety", "icon": "💎", "desc": "Avoid harsh chemicals when wearing emeralds or pearls."},
        {"id": "storage", "title": "Safe Storage", "icon": "📦", "desc": "Store pieces separately to prevent scratching and tangling."}
    ]
    
    return render(request, "preference_app/post_purchase.html", {
        "title": "Post-Purchase Hub",
        "orders": orders,
        "care_guides": care_guides
    })


@login_required
@require_POST
def save_style_profile(request):
    """AJAX view to save manual style preferences."""
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
        return JsonResponse({"error": str(e)}, status=500)


# ── Static Pages ──────────────────────────────────────────────────────────────

def about_view(request):
    """Render the About page."""
    return render(request, "preference_app/about.html")


def contact_view(request):
    """Render the Contact page."""
    return render(request, "preference_app/contact.html")


# ── Chatbot API ───────────────────────────────────────────────────────────────

@require_POST
def chat_api_view(request):
    """Handle incoming user message and return AI response."""
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        session_id   = data.get("session_id")
        
        if not user_message:
            return JsonResponse({"error": "Empty message"}, status=400)
            
        # Ensure user has a session or create one
        user = request.user if request.user.is_authenticated else None
        
        if not session_id:
            session = ChatSession.objects.create(user=user)
            session_id = session.id
        else:
            session = ChatSession.objects.filter(id=session_id).first()
            # Security check: if session belongs to a user, it must be the current user
            if session and session.user and session.user != user:
                # Unauthorized access to someone else's session
                session = ChatSession.objects.create(user=user)
                session_id = session.id
            elif not session:
                session = ChatSession.objects.create(user=user)
                session_id = session.id
            
        bot_reply, recommendations = get_chatbot_response(user, session_id, user_message)
        
        return JsonResponse({
            "session_id": session_id,
            "reply": bot_reply,
            "recommendations": recommendations
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def chat_history_view(request):
    """Retrieve history for a specific session."""
    session_id = request.GET.get("session_id")
    if not session_id:
        return JsonResponse({"messages": []})
        
    user = request.user if request.user.is_authenticated else None
    
    session = ChatSession.objects.filter(id=session_id).first()
    if not session:
        return JsonResponse({"messages": []})

    # Security check: if session belongs to a user, it must be the current user
    if session.user and session.user != user:
        return JsonResponse({"error": "Unauthorized"}, status=403)
        
    messages = ChatMessage.objects.filter(
        session=session
    ).order_by("timestamp")
    
    serialized = []
    for m in messages:
        serialized.append({
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat()
        })
    return JsonResponse({"messages": serialized})


# ── Virtual Try-On API ────────────────────────────────────────────────────────

@login_required
@require_POST
def tryon_api_view(request):
    """
    Handle AR Try-On requests.
    Expects: user_photo (file), item_id (int), item_type (string)
    """
    try:
        from preference_app.tryon_engine import process_tryon
        import os

        user_photo = request.FILES.get("photo")
        item_id    = request.POST.get("item_id")
        item_type  = request.POST.get("item_type")

        print(f"[TryOn Debug] item_id={item_id}  item_type={item_type}")
        print(f"[TryOn Debug] photo received: {user_photo}")

        if not user_photo:
            return JsonResponse({"error": "No photo uploaded"}, status=400)

        print(f"[TryOn Debug] photo name={user_photo.name}  size={user_photo.size} bytes")

        # Save photo to disk
        from django.conf import settings
        path      = default_storage.save(
            f"tmp/tryon_input_{request.user.id}.jpg",
            ContentFile(user_photo.read())
        )
        full_path = os.path.join(settings.MEDIA_ROOT, path)

        print(f"[TryOn Debug] saved to: {full_path}")
        print(f"[TryOn Debug] file exists: {os.path.exists(full_path)}")
        print(f"[TryOn Debug] file size on disk: {os.path.getsize(full_path)} bytes")

        # Test if OpenCV can read it
        import cv2
        img = cv2.imread(full_path)
        if img is None:
            print("[TryOn Debug] ❌ OpenCV CANNOT read the image")
            return JsonResponse({"error": "Image could not be read by OpenCV. Try a JPG or PNG file."}, status=400)
        else:
            print(f"[TryOn Debug] ✅ OpenCV read OK — shape: {img.shape}")

        # Run try-on
        result_path = process_tryon(full_path, item_id, item_type)

        print(f"[TryOn Debug] result_path={result_path}")

        if result_path:
            relative_url = f"{settings.MEDIA_URL}tryon/{os.path.basename(result_path)}"
            return JsonResponse({"result_url": relative_url})
        else:
            return JsonResponse({
                "error": "Could not detect face/hand. Please use a clear front-facing photo."
            }, status=400)

    except ModuleNotFoundError as e:
        return JsonResponse({"error": f"Try-on service unavailable: {e}"}, status=503)
    except Exception as e:
        import traceback
        print(f"[TryOn Debug] EXCEPTION: {traceback.format_exc()}")
        return JsonResponse({"error": str(e)}, status=500)


# In preference_app/views.py



def compute_visual_preference_scores(user):
    """Average CNN feature vectors of liked items → map to jewelry dimensions."""
    liked_items = SwipeResponse.objects.filter(
        session__user=user, action='like'
    ).select_related('item')

    if not liked_items.exists():
        return None  # No swipe data yet

    vectors = []
    for resp in liked_items:
        if resp.item.visual_features:
            vectors.append(json.loads(resp.item.visual_features))

    if not vectors:
        return None

    avg_vector = np.mean(vectors, axis=0)

    # Map the 1280-dim MobileNet vector to your 5 jewelry dimensions
    # Split the vector into 5 equal segments, take mean of each
    chunk = len(avg_vector) // 5
    return {
        'style_score':     float(np.mean(avg_vector[0:chunk])),
        'material_score':  float(np.mean(avg_vector[chunk:chunk*2])),
        'occasion_score':  float(np.mean(avg_vector[chunk*2:chunk*3])),
        'aesthetic_score': float(np.mean(avg_vector[chunk*3:chunk*4])),
        'budget_score':    float(np.mean(avg_vector[chunk*4:]))
    }