"""Step 3: talk to the LLM. Whichever keys are set are tried in order
OpenAI -> Groq -> Gemini; if all fail we still answer extractively from the
retrieved filings instead of crashing."""
import json
import re

import requests

import config


class LLMUnavailable(Exception):
    pass


def available():
    return bool(config.OPENAI_API_KEY or config.GROQ_API_KEY or config.GEMINI_API_KEY)


def _openai(messages, max_tokens, json_mode):
    last = None
    for model in config.OPENAI_MODELS:
        body = {"model": model, "messages": messages, "temperature": config.TEMPERATURE,
                "max_completion_tokens": max_tokens}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        for _ in range(2):
            try:
                r = requests.post("https://api.openai.com/v1/chat/completions",
                                  headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
                                  json=body, timeout=60)
            except requests.RequestException as e:
                last = f"{model}: {e}"
                break
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"], f"openai/{model}"
            last = f"{model}: HTTP {r.status_code} {r.text[:160]}"
            # Some newer models only accept the default temperature: retry once without it.
            if r.status_code == 400 and "temperature" in r.text and "temperature" in body:
                body.pop("temperature")
                continue
            if r.status_code in (401, 429):      # bad key / no quota: other models won't help
                raise LLMUnavailable(last)
            break
    raise LLMUnavailable(last)


def _groq(messages, max_tokens, json_mode):
    last = None
    for model in config.GROQ_MODELS:
        body = {"model": model, "messages": messages, "temperature": config.TEMPERATURE,
                "max_tokens": max_tokens}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
                              json=body, timeout=45)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"], f"groq/{model}"
            last = f"{model}: HTTP {r.status_code} {r.text[:160]}"
        except requests.RequestException as e:
            last = f"{model}: {e}"
    raise LLMUnavailable(last)


def _gemini(messages, max_tokens, json_mode):
    system = "\n".join(m["content"] for m in messages if m["role"] == "system")
    contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                for m in messages if m["role"] != "system"]
    gen = {"temperature": config.TEMPERATURE, "maxOutputTokens": max_tokens}
    if json_mode:
        gen["responseMimeType"] = "application/json"
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent")
    r = requests.post(url, headers={"x-goog-api-key": config.GEMINI_API_KEY},
                      json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
                            "generationConfig": gen}, timeout=60)
    if r.status_code != 200:
        raise LLMUnavailable(f"gemini HTTP {r.status_code} {r.text[:160]}")
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts), f"gemini/{config.GEMINI_MODEL}"


def chat(messages, max_tokens=900, json_mode=False):
    errors = []
    if config.OPENAI_API_KEY:
        try:
            return _openai(messages, max_tokens, json_mode)
        except LLMUnavailable as e:
            errors.append(str(e))
    if config.GROQ_API_KEY:
        try:
            return _groq(messages, max_tokens, json_mode)
        except LLMUnavailable as e:
            errors.append(str(e))
    if config.GEMINI_API_KEY:
        try:
            return _gemini(messages, max_tokens, json_mode)
        except LLMUnavailable as e:
            errors.append(str(e))
    raise LLMUnavailable("; ".join(errors) or "no API key configured")


def chat_json(messages, max_tokens=400):
    text, model = chat(messages, max_tokens=max_tokens, json_mode=True)
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text), model
