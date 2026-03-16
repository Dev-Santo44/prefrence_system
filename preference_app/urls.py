from django.urls import path
from preference_app import views

urlpatterns = [

    # ── Auth ─────────────────────────────────────────
    path('',               views.index_view,          name='index'),
    path('logout/',        views.logout_view,          name='logout'),

    # ── Survey ───────────────────────────────────────
    path('survey/',        views.survey_view,          name='survey'),
    path('survey/submit/', views.survey_submit_view,   name='survey_submit'),

    # ── Swipe ────────────────────────────────────────
    path('swipe/',         views.swipe_view,           name='swipe'),
    path('swipe/submit/',  views.submit_swipe,         name='submit_swipe'),

    # ── Dashboard ────────────────────────────────────
    path('dashboard/',     views.dashboard_view,       name='dashboard'),

    # ── Chat ─────────────────────────────────────────
    path('chat/message/',  views.chat_api_view,        name='chat_message'),
    path('chat/history/',  views.chat_history_view,    name='chat_history'),

    # ── Try-On ───────────────────────────────────────
    path('tryon/',         views.tryon_api_view,       name='tryon'),

    # ── Wishlist ─────────────────────────────────────
    path('wishlist/toggle/', views.wishlist_toggle,    name='wishlist_toggle'),

    # ── Separate Pages ───────────────────────────────
    path('look-builder/',  views.look_builder_view,    name='look_builder'),
    path('gallery/',       views.gallery_view,         name='gallery'),
    path('fit-guide/',     views.fit_guide_view,       name='fit_guide'),
    path('gifting/',       views.gifting_view,         name='gifting'),
    path('post-purchase/', views.post_purchase_view,    name='post_purchase'),
    path('style-profile/save/', views.save_style_profile, name='save_style_profile'),

    # ── Static Pages ─────────────────────────────────
    path('about/',         views.about_view,           name='about'),
    path('contact/',       views.contact_view,         name='contact'),
]