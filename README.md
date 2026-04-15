# ⚡ Ruvi AI — Smart AI Chatbot

A powerful AI assistant combining the best of ChatGPT, Claude, Perplexity, and Manus AI.

## ✨ Features

| Feature | Inspiration | What it does |
|---------|-------------|--------------|
| Natural Chat | ChatGPT | Smooth, context-aware conversation |
| Deep Reasoning | Claude | Breaks down complex problems step by step |
| Web Research | Perplexity | Searches web, reads pages, synthesizes answers |
| Task Planning | Manus AI | Plans multi-step tasks and executes them |
| User Memory | — | Remembers your name, location, preferences |

## 🚀 Quick Start (Local)

### Step 1: Get a Free Groq API Key
1. Go to → https://console.groq.com
2. Sign up (completely free, no credit card)
3. Click **"Create API Key"**
4. Copy the key

### Step 2: Set Up the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env

# Open .env and paste your Groq API key
# GROQ_API_KEY=your_key_here
```

### Step 3: Run
```bash
streamlit run app.py
```

Open your browser → http://localhost:8501

---

## ☁️ Deploy on Streamlit Cloud (Free, Public URL)

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Jarvis AI initial commit"
# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/jarvis-ai.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud
1. Go to → https://share.streamlit.io
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select your repository
5. Set **Main file**: `app.py`
6. Click **"Advanced settings"** → **Secrets**
7. Add this secret:
   ```
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
8. Click **Deploy!**

Your app will be live at: `https://your-app-name.streamlit.app`

---

## 📁 Project Structure

```
jarvis_ai/
├── app.py          ← Main UI (Streamlit)
├── brain.py        ← LLM reasoning (Groq + LLaMA 3)
├── actions.py      ← Web tools (DuckDuckGo search, web reading)
├── memory.py       ← User memory (persistent across chats)
├── requirements.txt
├── .env.example    ← API key template
└── README.md
```

## 🆓 All Free Tools Used

| Tool | Purpose | Cost |
|------|---------|------|
| Groq API | LLM (LLaMA 3.3 70B) | Free tier |
| DuckDuckGo | Web search | Free, no key |
| BeautifulSoup | Web reading | Free |
| Streamlit | UI + Deployment | Free |

## 💡 Usage Tips

- Say **"search for..."** to trigger web research
- Say **"write code for..."** to trigger deep reasoning
- Tell Jarvis your name/location — it will remember
- Toggle **"Force Web Search"** in sidebar to always search
- Toggle **"Deep Reasoning"** for complex coding/math tasks
