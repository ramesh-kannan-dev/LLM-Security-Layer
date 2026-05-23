# Archias: LLM Security Firewall 🛡️

Hey there! Welcome to my final-year Computer Science engineering project. 

With AI tools like ChatGPT and Gemini becoming so popular, "prompt injections" and "jailbreaks" (where users trick the AI into doing things it shouldn't) are becoming a massive security issue. I built **Archias** to solve this. It acts as a security layer that sits between the user and the language model, intercepting and analyzing prompts before they are ever processed. 

Everything here is strictly software and Python-based—no hardware dependencies required. 

## How It Works
I designed a two-step defense system to keep the chat secure:

1. **The Fast Filter (Layer 1):** A strict, hardcoded firewall that immediately catches and blocks obvious malicious keywords, illegal terms, and standard bypass phrases.
2. **The AI Guard (Layer 2):** For the sneaky stuff, I trained a sequence classification model to detect complex prompt injections. I specifically used the standard **BERT** model (not RoBERTa or heavier variants) to keep the architecture focused and efficient. It evaluates the user's text and assigns a confidence score. If it thinks the prompt is a jailbreak attempt, it blocks it. If it's safe, it passes it through to the Gemini API.

## What I Used (Tech Stack)
* **Backend:** Python & Flask
* **Machine Learning:** PyTorch, HuggingFace Transformers (BERT)
* **LLM:** Google Gemini 2.5 Flash API
* **Database:** SQLite (for tracking blocked prompts in an admin dashboard)
* **Frontend:** Clean HTML/CSS/JS with a streaming typing effect

## How to Run It Locally
If you want to pull this code and run it on your own machine:

1. Clone the repo.
2. Install the requirements: `pip install -r requirements.txt` (Note: It uses the CPU version of PyTorch to keep it lightweight).
3. Add your own Gemini API key in `app.py`.
4. Run `python app.py` and open `localhost:5000` in your browser.

---
*Built from scratch as my final-year AI project.*
