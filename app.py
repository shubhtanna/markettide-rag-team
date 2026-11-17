"""
app.py - Root entry point for Market Tide RAG Chatbot.

Run directly via Streamlit:
    streamlit run app.py

Or run via Python:
    python app.py
"""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CHATBOT_DIR = os.path.join(ROOT_DIR, "chatbot")

if CHATBOT_DIR not in sys.path:
    sys.path.insert(0, CHATBOT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Auto-launch streamlit if executed directly via python app.py
if __name__ == "__main__" and not any("streamlit" in arg for arg in sys.argv):
    import subprocess
    print("🚀 Launching Market Tide RAG Chatbot on http://localhost:8501 ...")
    cmd = [sys.executable, "-m", "streamlit", "run", __file__] + sys.argv[1:]
    subprocess.run(cmd)
    sys.exit(0)

# Execute the core chatbot application
chatbot_main = os.path.join(CHATBOT_DIR, "app.py")
with open(chatbot_main, "r", encoding="utf-8") as f:
    code = f.read()

exec(compile(code, chatbot_main, "exec"), globals())
