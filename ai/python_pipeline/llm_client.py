import os
from dotenv import load_dotenv

# Ensure module-local .env is loaded (helps when running from project root)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

try:
    import openai
except Exception:
    openai = None

try:
    import google.genai as genai
except Exception:
    try:
        from google import genai
    except Exception:
        genai = None

try:
    from .config import OPENAI_API_KEY
except ImportError:
    from config import OPENAI_API_KEY


class LLMClient:
    """Simple LLM client supporting Gemini and OpenAI."""

    def __init__(self, api_key=None, provider=None):
        self.provider = (provider or os.getenv('LLM_PROVIDER') or 'gemini').lower()
        self.default_model = os.getenv('LLM_MODEL')
        self._init_error = None

        if self.provider == 'openai':
            self.api_key = api_key or OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
        else:
            self.api_key = api_key or os.getenv('GOOGLE_API_KEY')

        self._client = None
        self._client_name = None
        if self.provider == 'openai' and openai and self.api_key:
            openai.api_key = self.api_key
            self._client = openai
            self._client_name = 'openai'
        elif self.provider in ('gemini', 'google') and genai:
            try:
                self._client = genai.Client(api_key=self.api_key) if self.api_key else genai.Client()
                self._client_name = 'genai'
            except Exception:
                self._client = None
                self._client_name = None
                self._init_error = 'genai client init failed'
        elif self.provider in ('gemini', 'google') and not genai:
            self._init_error = 'genai import failed'
        elif self.provider == 'openai' and (not openai or not self.api_key):
             self._init_error = 'openai client missing or API key unavailable'

    def complete(self, prompt, model=None, max_tokens=2048, temperature=0.2):
        model = model or self.default_model

        def clean_response(resp_dict):
            if isinstance(resp_dict, dict) and 'text' in resp_dict:
                text = resp_dict['text']
                if text and '<think>' in text:
                    import re
                    text = re.sub(r'<think>[\s\S]*?</think>', '', text).strip()
                    if '<think>' in text:
                        text = re.sub(r'<think>[\s\S]*', '', text).strip()
                    resp_dict['text'] = text
            return resp_dict

        # Direct routing for Groq models
        if model and ('llama' in model.lower() or 'mixtral' in model.lower() or 'gemma' in model.lower() or 'qwen' in model.lower()):
            return clean_response(self._complete_groq(prompt, max_tokens, temperature, model=model))

        if self.provider in ('gemini', 'google'):
            # Try Gemini first
            if self._client_name == 'genai' and self._client is not None:
                gemini_model = model or 'gemini-2.0-flash'
                try:
                    resp = self._client.models.generate_content(
                        model=gemini_model,
                        contents=prompt,
                        config={
                            'temperature': temperature,
                            'max_output_tokens': max_tokens,
                        },
                    )
                    text = getattr(resp, 'text', None) or str(resp)
                    if text:
                        return clean_response({'text': text, 'raw': resp, 'model': gemini_model})
                except Exception as e:
                    import logging
                    log = logging.getLogger(__name__)
                    log.warning(f"Gemini call failed ({e}). Falling back to Groq...")

            # If Gemini failed or client not initialized, fall back to Groq
            groq_resp = self._complete_groq(prompt, max_tokens, temperature)
            if not groq_resp.get('text', '').startswith('[[Groq error]]'):
                return clean_response(groq_resp)

            # If both failed, return error
            suffix = f' ({self._init_error})' if self._init_error else ''
            return clean_response({'text': f'[[Gemini error]] Gemini failed and Groq fallback failed: {groq_resp.get("text")}'})

        if self._client_name == 'openai' and self._client is not None:
            model = model or 'gpt-4o-mini'
            try:
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=[{'role': 'user', 'content': prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                text = resp['choices'][0]['message']['content']
                return clean_response({'text': text, 'raw': resp, 'model': model})
            except Exception as e:
                return clean_response({'text': f'[[OpenAI error]] {e} {prompt[:200]}'})

        # Try Groq directly if provider is groq
        if self.provider == 'groq':
            return clean_response(self._complete_groq(prompt, max_tokens, temperature))

        suffix = f' ({self._init_error})' if self._init_error else ''
        return clean_response({'text': '[[LLM unavailable]]' + suffix + ' ' + prompt[:200]})

    def _complete_groq(self, prompt, max_tokens=512, temperature=0.2, model=None):
        import requests
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            return {'text': '[[Groq error]] GROQ_API_KEY is not set'}

        model = model or os.getenv('GROQ_MODEL') or 'llama-3.3-70b-versatile'
        url = 'https://api.groq.com/openai/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature,
            'max_tokens': max_tokens
        }

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            if resp.status_code == 200:
                resp_json = resp.json()
                text = resp_json['choices'][0]['message']['content']
                return {'text': text, 'raw': resp_json, 'model': model}
            else:
                return {'text': f'[[Groq error]] status {resp.status_code}: {resp.text}'}
        except Exception as e:
            return {'text': f'[[Groq error]] request failed: {e}'}
