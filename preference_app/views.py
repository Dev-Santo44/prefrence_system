"""
Django Views for AI-Driven Personal Preference Identifier.
Handles: login, register, logout, survey, survey submit, dashboard.
"""

import sys
import os
import json

import numpy as np

from .models import SwipeResponse, JewelryCatalog, PreferenceResult

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

@login_required
def swipe_view(request):
    """Render the swipe matching interface."""
    return render(request, "preference_app/swipe.html")

@login_required
def swipe_images_api(request):
    """Returns 20 randomized jewelry images for the user to swipe."""
    import random
    
    all_items = list(JewelryCatalog.objects.all().values("id", "name", "image_url", "item_type", "style"))
    if len(all_items) > 20:
        samples = random.sample(all_items, 20)
    else:
        samples = all_items
        
    return JsonResponse({"items": samples})

@login_required
@require_POST
def swipe_submit_view(request):
    """
    Handle AJAX swipe submission (liked and disliked IDs).
    Fuses the visual scores into the existing preference record.
    """
    try:
        body = json.loads(request.body)
        liked_ids = body.get("liked_ids", [])
        disliked_ids = body.get("disliked_ids", [])
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "Invalid payload."}, status=400)

    user = request.user
    
    # 1. Log responses
    session = SwipeSession.objects.create(user=user)
    
    likes = JewelryCatalog.objects.filter(id__in=liked_ids)
    for item in likes:
        SwipeResponse.objects.create(session=session, item=item, action="like")
        
    dislikes = JewelryCatalog.objects.filter(id__in=disliked_ids)
    for item in dislikes:
        SwipeResponse.objects.create(session=session, item=item, action="dislike")
        
    # 2. Score Fusion
    # Retrieve existing survey answers (or empty if none)
    likert_answers = {}
    user_responses = Response.objects.filter(user=user)
    
    for r in user_responses:
        trait = r.question.category
        if trait not in likert_answers:
            likert_answers[trait] = []
        likert_answers[trait].append(float(r.answer))
        
    # Fuse base survey + swipe likes
    result = score_and_recommend(likert_answers, None, liked_ids)
    
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


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard_view(request):
    """Display OCEAN results and recommendations."""
    try:
        result = request.user.preference_result
    except PreferenceResult.DoesNotExist:
        messages.warning(request, "You haven't taken the survey yet.")
        return redirect("survey")

    return render(request, "preference_app/dashboard.html", {
        "result":       result,
        "result_json":  json.dumps(result.as_dict()),
    })


# ── Static Pages ──────────────────────────────────────────────────────────────

def about_view(request):
    """Render the About page."""
    return render(request, "preference_app/about.html")


def contact_view(request):
    """Render the Contact page."""
    return render(request, "preference_app/contact.html")


# ── Chatbot API ───────────────────────────────────────────────────────────────

@login_required
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
        if not session_id:
            session = ChatSession.objects.create(user=request.user)
            session_id = session.id
        else:
            session = ChatSession.objects.filter(id=session_id, user=request.user).first()
            if not session:
                session = ChatSession.objects.create(user=request.user)
                session_id = session.id
            
        bot_reply, recommendations = get_chatbot_response(request.user, session_id, user_message)
        
        return JsonResponse({
            "session_id": session_id,
            "reply": bot_reply,
            "recommendations": recommendations
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def chat_history_view(request):
    """Retrieve history for a specific session."""
    session_id = request.GET.get("session_id")
    if not session_id:
        return JsonResponse({"messages": []})
        
    messages = ChatMessage.objects.filter(
        session__id=session_id, 
        session__user=request.user
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
        user_photo = request.FILES.get("photo")
        item_id    = request.POST.get("item_id")
        item_type  = request.POST.get("item_type")
        
        if not user_photo:
            return JsonResponse({"error": "No photo uploaded"}, status=400)
            
        from django.conf import settings
        import os
        
        # Save temp user photo
        path = default_storage.save(f"tmp/tryon_input_{request.user.id}.jpg", ContentFile(user_photo.read()))
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        
        # Process AR
        result_path = process_tryon(full_path, item_id, item_type)
        
        if result_path:
            relative_url = f"{settings.MEDIA_URL}tryon/{os.path.basename(result_path)}"
            return JsonResponse({"result_url": relative_url})
        else:
            return JsonResponse({"error": "Failed to detect landmarks. Please ensure your face/hand is clearly visible."}, status=400)
            
    except Exception as e:
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