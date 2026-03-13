"""Admin configuration for preference_app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from preference_app.models import User, SurveyQuestion, Response, PreferenceResult, JewelryCatalog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ("email", "name", "role", "is_active", "created_at")
    list_filter    = ("role", "is_active")
    search_fields  = ("email", "name")
    ordering       = ("-created_at",)
    fieldsets      = (
        (None,           {"fields": ("email", "password")}),
        ("Personal",     {"fields": ("name", "role")}),
        ("Permissions",  {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets  = (
        (None, {"classes": ("wide",), "fields": ("email", "name", "role", "password1", "password2")}),
    )


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display  = ("id", "category", "question_text")
    list_filter   = ("category",)
    search_fields = ("question_text",)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "answer", "timestamp")
    list_filter  = ("question__category",)


@admin.register(PreferenceResult)
class PreferenceResultAdmin(admin.ModelAdmin):
    list_display = (
        "user", "style_score", "material_score",
        "occasion_score", "aesthetic_score", "budget_score"
    )


@admin.register(JewelryCatalog)
class JewelryCatalogAdmin(admin.ModelAdmin):
    list_display = ("thumbnail_tag", "name", "item_type", "material", "price_range")
    list_filter  = ("item_type", "style", "material", "occasion", "aesthetic", "price_range")
    search_fields = ("name",)
    readonly_fields = ("thumbnail_tag",)

    def thumbnail_tag(self, obj):
        from django.utils.html import format_html
        if obj.image_url:
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 5px;" />', obj.image_url)
        return "-"
    thumbnail_tag.short_description = "Preview"
