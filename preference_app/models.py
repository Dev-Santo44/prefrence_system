"""
Django ORM Models for AI-Driven Personal Preference Identifier.
Mirrors database/schema.sql using Django's custom AbstractBaseUser.
"""

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# ── Custom User Manager ───────────────────────────────────────────────────────

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, role="user"):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user  = self.model(email=email, name=name, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        user = self.create_user(email, name, password, role="admin")
        user.is_staff      = True
        user.is_superuser  = True
        user.save(using=self._db)
        return user


# ── User ─────────────────────────────────────────────────────────────────────

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [("user", "User"), ("admin", "Admin")]

    name       = models.CharField(max_length=255)
    email      = models.EmailField(unique=True)
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = "User"

    def __str__(self):
        return f"{self.name} <{self.email}>"


# ── Survey Question ───────────────────────────────────────────────────────────

class SurveyQuestion(models.Model):
    CATEGORY_CHOICES = [
        ("Style",     "Style Preference"),
        ("Material",  "Material Preference"),
        ("Occasion",  "Occasion Type"),
        ("Aesthetic", "Design Aesthetic"),
        ("Budget",    "Budget Range"),
    ]

    question_text = models.TextField()
    category      = models.CharField(max_length=30, choices=CATEGORY_CHOICES)

    class Meta:
        db_table  = "survey_questions"
        ordering  = ["category", "id"]

    def __str__(self):
        return f"[{self.category}] {self.question_text[:60]}"


# ── Response ──────────────────────────────────────────────────────────────────

class Response(models.Model):
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name="responses")
    question  = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    answer    = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "responses"

    def __str__(self):
        return f"User {self.user_id} | Q{self.question_id} → {self.answer}"


# ── Preference Result ─────────────────────────────────────────────────────────

class PreferenceResult(models.Model):
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preference_result")
    style_score     = models.FloatField(default=0)
    material_score  = models.FloatField(default=0)
    occasion_score  = models.FloatField(default=0)
    aesthetic_score = models.FloatField(default=0)
    budget_score    = models.FloatField(default=0)
    jewelry_persona = models.CharField(max_length=100, blank=True)
    recommendations = models.TextField(blank=True)
    
    # ── Manual Style Profile ──
    metal_preference     = models.CharField(max_length=50, blank=True)
    style_aesthetic  = models.CharField(max_length=50, blank=True)
    stone_preference     = models.CharField(max_length=50, blank=True)
    
    created_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "preference_results"

    def __str__(self):
        return f"Results for {self.user.name}"

    def as_dict(self):
        return {
            "style":           round(self.style_score, 1),
            "material":        round(self.material_score, 1),
            "occasion":        round(self.occasion_score, 1),
            "aesthetic":       round(self.aesthetic_score, 1),
            "budget":          round(self.budget_score, 1),
            "persona":         self.jewelry_persona,
            "recommendations": self.recommendations,
        }


# ── Jewelry Catalog ───────────────────────────────────────────────────────────

class JewelryCatalog(models.Model):
    name         = models.CharField(max_length=255)
    item_type    = models.CharField(max_length=100)  # Necklace, Ring, etc.
    style        = models.CharField(max_length=100, db_index=True)  # Minimalist, Statement
    material     = models.CharField(max_length=100, db_index=True)  # Gold, Silver, Artificial
    occasion     = models.CharField(max_length=100, db_index=True)  # Casual, Bridal, Party
    aesthetic    = models.CharField(max_length=100)  # Traditional, Western
    price        = models.IntegerField(default=0)    # Raw price in INR
    price_range  = models.CharField(max_length=50, db_index=True, blank=True)   # Economy, Mid-range, Luxury
    image_url    = models.URLField(max_length=500, blank=True)
    product_link = models.URLField(max_length=500, blank=True)
    visual_features = models.JSONField(null=True, blank=True) # 1280-d MobileNetV2 vector

    class Meta:
        db_table = "jewelry_catalog"

    def save(self, *args, **kwargs):
        # Auto-compute price_range if not provided based on raw price
        if self.price < 5000:
            self.price_range = "Economy"
        elif 5000 <= self.price <= 20000:
            self.price_range = "Mid-range"
        else:
            self.price_range = "Luxury"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.item_type}) - ₹{self.price}"

class SwipeSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "swipe_sessions"

class SwipeResponse(models.Model):
    session = models.ForeignKey(SwipeSession, on_delete=models.CASCADE, related_name='responses')
    item = models.ForeignKey(JewelryCatalog, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=[('like', 'Like'), ('dislike', 'Dislike')])

    class Meta:
        db_table = "swipe_responses"


class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions", null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_sessions"

    def __str__(self):
        return f"Session {self.id} for {self.user.name}"

class ChatMessage(models.Model):
    ROLE_CHOICES = [("user", "User"), ("assistant", "Assistant")]
    
    session   = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role      = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content   = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


# ── Wishlist ──────────────────────────────────────────────────────────────────

class Wishlist(models.Model):
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    item      = models.ForeignKey(JewelryCatalog, on_delete=models.CASCADE)
    added_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table          = "wishlist"
        unique_together   = ("user", "item")
        ordering          = ["-added_at"]

    def __str__(self):
        return f"{self.user.name} ♥ {self.item.name}"


# ── Recently Viewed ──────────────────────────────────────────────────────────

class RecentlyViewed(models.Model):
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="viewed_items")
    item      = models.ForeignKey(JewelryCatalog, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recently_viewed"
        ordering = ["-viewed_at"]
        unique_together = ("user", "item")

    def __str__(self):
        return f"{self.user.name} viewed {self.item.name}"


# ── Cart ──────────────────────────────────────────────────────────────────────

class CartItem(models.Model):
    user     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    item     = models.ForeignKey(JewelryCatalog, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "cart_items"
        unique_together = ("user", "item")
        ordering        = ["-added_at"]

    def __str__(self):
        return f"{self.user.name}'s Cart: {self.item.name} (x{self.quantity})"

    @property
    def total_price(self):
        return self.item.price * self.quantity
