"""
Multi-provider AI service with automatic fallback.
Primary: Claude (Anthropic)
Fallback 1: OpenAI GPT-4o
Fallback 2: Google Gemini 2.0 Flash
Env vars: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY
Only ANTHROPIC_API_KEY is required. Others are optional fallbacks.
"""
import os
import json


async def ai_complete(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    """Try Claude first, fall back to OpenAI, then Gemini."""
    errors = []

    # Try 1: Claude (primary)
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text
        except Exception as e:
            errors.append(f"Claude: {e}")
            print(f"[AI] Claude failed: {e}, trying OpenAI...")

    # Try 2: OpenAI (fallback)
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            errors.append(f"OpenAI: {e}")
            print(f"[AI] OpenAI failed: {e}, trying Gemini...")

    # Try 3: Google Gemini (fallback)
    google_key = os.environ.get("GOOGLE_API_KEY")
    if google_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=google_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(
                f"{system_prompt}\n\n{user_prompt}"
            )
            return response.text
        except Exception as e:
            errors.append(f"Gemini: {e}")
            print(f"[AI] Gemini failed: {e}")

    raise Exception(f"All AI providers failed: {'; '.join(errors)}")
