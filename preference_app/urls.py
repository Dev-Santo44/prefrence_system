from django.urls import path
from preference_app import views

print("DEBUG: preference_app/urls.py loaded")

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
    path('ar-tryon/',      views.ar_tryon_view,        name='ar_tryon'),


    # ── Wishlist ─────────────────────────────────────
    path('wishlist/toggle/', views.wishlist_toggle,    name='wishlist_toggle'),

    # ── Separate Pages ───────────────────────────────
    path('look-builder/',  views.look_builder_view,    name='look_builder'),
    path('gallery/',       views.gallery_view,         name='gallery'),
    path('fit-guide/',     views.fit_guide_view,       name='fit_guide'),
    path('gifting/',       views.gifting_view,         name='gifting'),
    path('post-purchase/', views.post_purchase_view,    name='post_purchase'),
    path('style-profile/save/', views.save_style_profile, name='save_style_profile'),

    # ── Cart & Checkout ──────────────────────────────
    path('cart/',           views.cart_view,           name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/',       views.checkout_view,        name='checkout'),
    path('checkout/<int:product_id>/', views.checkout_view, name='checkout_item'),
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail_page'),

    # ── APIs ─────────────────────────────────────────
    path('api/view-product/<int:product_id>/', views.view_product_api, name='view_product_api'),
    path('api/product-detail/<int:product_id>/', views.product_detail_api, name='product_detail_api'),

    # ── Static Pages ─────────────────────────────────
    path('about/',         views.about_view,           name='about'),
    path('contact/',       views.contact_view,         name='contact'),
    path('explore/',       views.explore_view,         name='explore'),
    path('trending/',      views.trending_view,        name='trending'),
    path('api/gcs-proxy/', views.gcs_proxy,            name='gcs_proxy'),
]