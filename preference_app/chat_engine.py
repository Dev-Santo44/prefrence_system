import os
import re
import json
from anthropic import Anthropic
from .models import ChatSession, ChatMessage, JewelryCatalog
from django.db.models import Q

# Initialize client
# Note: Ensure ANTHROPIC_API_KEY is in .env or environment
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """
You are the "PreferenceAI Jewelry Advisor," a sophisticated, high-end AI assistant. 
Your goal is to help users discover jewelry that perfectly matches their style, occasion, and budget.

Follow this flow:
1. Greet the user warmly and ask about the occasion or style they are looking for.
2. If they provide details, refine their preferences (Material: Gold/Silver/Platinum, Style: Minimalist/Statement, Budget: Economy/Mid-range/Luxury).
3. Once you have enough info, provide a personalized advice and recommendation.

CRITICAL: When you are ready to suggest specific categories, include a structured data block at the end of your message in this EXACT format:
[TAGS: style=MINIMALIST; material=GOLD; occasion=BRIDAL; budget=MID-RANGE]

Available Values:
- style: Minimalist, Statement, Traditional, Western
- material: Gold, Silver, Diamond, Platinum, Artificial
- occasion: Casual, Bridal, Party, Formal, Ethnic
- budget: Economy, Mid-range, Luxury

Keep your tone premium, elegant, and helpful. Do not mention that you are an AI unless asked.
"""

def get_chatbot_response(user, session_id, user_message):
    """
    Main entry point for chat messages.
    Returns: (text_reply, recommendations_list)
    """
    session = ChatSession.objects.get(id=session_id)
    
    # Persistent history
    history = ChatMessage.objects.filter(session=session).order_by('timestamp')
    messages = []
    
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    
    # Add new user message
    messages.append({"role": "user", "content": user_message})
    
    # Save user message to DB
    ChatMessage.objects.create(session=session, role="user", content=user_message)
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        
        bot_reply = response.content[0].text
        
        # Save assistant message to DB
        ChatMessage.objects.create(session=session, role="assistant", content=bot_reply)
        
        # Extract tags
        tags = extract_tags(bot_reply)
        
        # Fetch recommendations if tags exist
        recommendations = []
        if tags:
            recommendations = query_catalog(tags)
            # Remove the tag block from the user-facing reply to keep it clean
            bot_reply = re.sub(r'\[TAGS:.*?\]', '', bot_reply).strip()
            
        return bot_reply, recommendations
        
    except Exception as e:
        print(f"Chatbot Error: {e}")
        return "I apologize, but I'm having trouble connecting to my creative engine. Please try again in a moment.", []

def extract_tags(text):
    """Parses [TAGS: style=X; material=Y; ...] format"""
    match = re.search(r'\[TAGS: (.*?)\]', text)
    if not match:
        return None
        
    tag_str = match.group(1)
    tags = {}
    for part in tag_str.split(';'):
        if '=' in part:
            k, v = part.strip().split('=')
            tags[k.lower()] = v.strip()
    return tags

def query_catalog(tags):
    """Queries JewelryCatalog based on extracted tags"""
    query = Q()
    
    if tags.get('style'):
        query &= Q(style__icontains=tags['style'])
    if tags.get('material'):
        query &= Q(material__icontains=tags['material'])
    if tags.get('occasion'):
        query &= Q(occasion__icontains=tags['occasion'])
    if tags.get('budget'):
        query &= Q(price_range__iexact=tags['budget'])
        
    # Return top 3 matches
    results = JewelryCatalog.objects.filter(query)[:3]
    
    serialized = []
    for item in results:
        serialized.append({
            "id": item.id,
            "name": item.name,
            "price": item.price,
            "image": item.image_url,
            "link": item.product_link,
            "style": item.style,
            "material": item.material
        })
    return serialized
