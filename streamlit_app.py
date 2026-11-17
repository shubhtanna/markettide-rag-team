"""
streamlit_app.py - Standard Streamlit Cloud entry point for Market Tide RAG Chatbot.
"""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CHATBOT_DIR = os.path.join(ROOT_DIR, "chatbot")

if CHATBOT_DIR not in sys.path:
    sys.path.insert(0, CHATBOT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

chatbot_main = os.path.join(CHATBOT_DIR, "app.py")
with open(chatbot_main, "r", encoding="utf-8") as f:
    code = f.read()

exec(compile(code, chatbot_main, "exec"), globals())
