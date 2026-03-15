"""URL patterns for preference_app."""

from django.urls import path
from preference_app import views

urlpatterns = [
    path("",           views.index_view,         name="index"),
    path("logout/",    views.logout_view,         name="logout"),
    path("survey/",    views.survey_view,         name="survey"),
    path("survey/submit/", views.survey_submit_view, name="survey_submit"),
    path("dashboard/", views.dashboard_view,      name="dashboard"),
    path("about/",     views.about_view,          name="about"),
    path("contact/",   views.contact_view,        name="contact"),
    path("swipe/",     views.swipe_view,          name="swipe"),
    
    path("swipe/images/", views.swipe_images_api, name="swipe_images"),
    path("swipe/submit/", views.swipe_submit_view, name="swipe_submit"),

    path("chat/message/", views.chat_api_view,      name="chat_message"),
    path("chat/history/", views.chat_history_view,  name="chat_history"),
    path("tryon/process/", views.tryon_api_view,    name="tryon_process"),
]
