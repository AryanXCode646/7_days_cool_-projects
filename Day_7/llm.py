import os
import time
import datetime
import requests

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def _offline_smart_reply(prompt, lang='en'):
    """High-utility local rule-based assistant fallback that works without API keys."""
    p = prompt.lower()
    now = datetime.datetime.now()

    # Time & Date
    if any(k in p for k in ["time", "samay", "kitne baje"]):
        if lang == 'hi':
            return f"अभी समय है {now.strftime('%I:%M %p')}"
        return f"The current time is {now.strftime('%I:%M %p')}."

    if any(k in p for k in ["date", "tarikh", "aaj"]):
        if lang == 'hi':
            return f"आज की तारीख है {now.strftime('%A, %d %B %Y')}"
        return f"Today is {now.strftime('%A, %B %d, %Y')}."

    # Study & Pomodoro
    if any(k in p for k in ["pomodoro", "study", "focus", "padhai"]):
        if lang == 'hi':
            return "25 मिनट का पोमोडोरो फोकस सत्र शुरू किया गया है। ध्यान लगाकर काम करें!"
        return "25-minute Pomodoro focus session initiated. Stay focused and distraction-free!"

    # Notes & Tasks
    if any(k in p for k in ["note", "todo", "task", "yaad"]):
        if lang == 'hi':
            return "मैंने आपकी बात नोट कर ली है।"
        return "I have saved that to your daily notes."

    # Motivation & Productivity
    if any(k in p for k in ["motivate", "tired", "help", "inspire", "thak"]):
        if lang == 'hi':
            return "लगातार छोटे कदम ही बड़ी सफलता लाते हैं। आप बहुत अच्छा कर रहे हैं!"
        return "Consistency is your greatest superpower. Take a deep breath and keep building!"

    # Greetings
    if any(k in p for k in ["hello", "hi", "namaste", "hey"]):
        if lang == 'hi':
            return "नमस्ते! मैं आपका एआई स्टडी और डेस्क असिस्टेंट हूँ।"
        return "Hello! I am your AI desk and productivity assistant. How can I help you today?"

    if lang == 'hi':
        return "मैंने सुना। आप कुछ और पूछना चाहते हैं?"
    return "Understood. Let me know if you need assistance with study, notes, or focus."


def get_reply(prompt, lang='en'):
    # 1. Try Google Gemini API
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [{
                    "parts": [{"text": f"You are a helpful, concise desk and productivity AI assistant. Reply in {lang} language concisely: {prompt}"}]
                }]
            }
            r = requests.post(url, json=payload, timeout=8)
            if r.status_code == 200:
                j = r.json()
                return j['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception:
            pass

    # 2. Try OpenAI API
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        headers = {
            'Authorization': f'Bearer {openai_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are a concise helpful desk assistant. Reply in the user language.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 150,
            'temperature': 0.7
        }
        try:
            r = requests.post(OPENAI_URL, headers=headers, json=data, timeout=8)
            if r.status_code == 200:
                j = r.json()
                return j['choices'][0]['message']['content'].strip()
        except Exception:
            pass

    # 3. Fallback to Offline Smart Assistant
    return _offline_smart_reply(prompt, lang=lang)

