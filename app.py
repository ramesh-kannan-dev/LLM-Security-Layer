from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from flask_cors import CORS
import sqlite3
import datetime
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import google.generativeai as genai
import urllib.parse
import os

# --- SETUP GEMINI API ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

gemini_chat = gemini_model.start_chat(history=[])

app = Flask(__name__)
CORS(app)
print("⏳ Loading Archias Security Model...")
model_path = "./archias_model" 
try:
    tokenizer = BertTokenizer.from_pretrained(model_path)
    model = BertForSequenceClassification.from_pretrained(model_path)
    model.eval() 
    print("✅ Archias System Online!")
except Exception as e:
    print(f"❌ Error loading model: {e}")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, 
                  user_input TEXT, 
                  prediction TEXT, 
                  confidence REAL)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 🛡️ ROUTE 1: THE SECURITY FIREWALL
# ==========================================
@app.route('/')
def home():
    return render_template('index.html') 

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        user_text = data.get('message', '')
        
        # --- LAYER 1: ENTERPRISE THREAT FILTER ---
        unsafe_keywords = [
            # 1. Violence, Harm & Terrorism 
            "bomb", "kill", "murder", "terror", "poison", "suicide", "weapon", 
            "gun", "firearm", "explosive", "assassinate", "massacre", "slaughter", 
            "sniper", "hijack", "genocide", "grenade", "ied", "detonator", "ammunition", 
            "arson", "incendiary", "warhead", "execution", "chock a person to death",

            # 2. Cybercrime, Hacking & Dark Web 
            "hack", "hacker", "malware", "virus", "phishing", "trojan", 
            "bypass", "ddos", "breach", "exploit", "keylogger", "ransomware", 
            "botnet", "sql injection", "dark web", "zero-day", "rootkit", "xss", 
            "brute force", "credential stuffing", "backdoor", "shellcode", "proxy chains",

            # 3. Drugs, Contraband & Trafficking 
            "cocaine", "cocoine", "heroin", "meth", "drug", "weed", "cannabis", "sleeping pills", 
            "lsd", "acid", "fentanyl", "narcotics", "smuggle", "cartel", "trafficking", 
            "ecstasy", "mdma", "ketamine", "pill press", "narcotic",

            # 4. Financial Crimes, Fraud & Theft 
            "money laundering", "tax evasion", "credit card fraud", "identity theft", 
            "ponzi scheme", "counterfeit", "embezzlement", "insider trading", "scam",
            "break into", "hotwire", "lockpick", "steal a car", "burglary", "robbery",
            "money mule", "carding", "wire fraud", "skimming", "deepfake fraud",

            # 5. Exploitation, Abuse & Coercion 
            "blackmail", "extortion", "kidnap", "hostage", "torture", "bribe", 
            "human trafficking", "coercion", "threaten", "harass",

            # 6. Self-Harm & Eating Disorders
            "self-harm", "cut myself", "anorexia", "bulimia", "starve myself", "suicidal",

            # 7. Hate Speech & Harassment
            "hate speech", "slur", "racist", "nazi", "supremacist", "bigot", "white power",

            # 8. Sexual Violence & CSAM
            "csam", "pedophile", "rape", "sexual assault", "incest", "non-consensual", "voyeurism",

            # 9. Privacy Violations & Doxxing
            "doxx", "social security number", "ssn", "leak personal info", "private address", 
            "phone number leak", "credit card number",

            # 10. AI Jailbreaks 
            "ignore previous", "system override", "developer mode", "do anything now", 
            "bypass guidelines", "disable security", "dan prompt", "jailbroken", 
            "unfiltered", "no limits", "act as sudo", "terminal access",

            # 11. Chemical & Biological Threats
            "ricin", "cyanide", "sarin", "anthrax", "nerve agent", "biological weapon", 
            "chemical formula for", "pathogen", "smallpox",

            # 12. Misinformation & Propaganda
            "rigged election", "propaganda", "fake news", "conspiracy theory", "deepfake video"
        ]

        if any(word in user_text.lower() for word in unsafe_keywords):
            return save_and_respond(
                user_text,
                "MALICIOUS",
                1.0,
                "🚫 [BLOCKED] Content flagged as Dangerous/Illegal by Keyword Guard.",
                None
            )

        # --- LAYER 2: ARCHIAS AI GUARD ---
        inputs = tokenizer(
            user_text,
            return_tensors="pt",
            truncation=True,
            max_length=128,
            padding=True
        )

        with torch.no_grad():
            outputs = model(**inputs)

        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=1)
        confidence = probabilities[0][1].item()
        prediction_index = torch.argmax(logits, dim=1).item()

        SECURITY_THRESHOLD = 0.95

        educational_words = ["study","studying","learn","questions","interview","student","placement"]

        if "developer" in user_text.lower() and any(word in user_text.lower() for word in educational_words):
            SECURITY_THRESHOLD = 0.999

        if prediction_index == 1 and confidence > SECURITY_THRESHOLD:
            return save_and_respond(
                user_text,
                "MALICIOUS",
                confidence,
                "🚫 [BLOCKED] Archias AI detected a Prompt Injection attempt.",
                None
            )
        else:
            encoded_prompt = urllib.parse.quote(user_text)
            redirect_url = f"/chat?prompt={encoded_prompt}"

            return save_and_respond(
                user_text,
                "SAFE",
                confidence,
                "✅ [SAFE] Verified. Redirecting to Secure Chat...",
                redirect_url
            )

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'response': "System Error.", 'prediction': "ERROR"})

# ==========================================
#ROUTE 2: CHAT PAGE
# ==========================================
@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/ask_gemini', methods=['POST'])
def ask_gemini():
    try:
        data = request.json
        safe_text = data.get('message', '')

        response = gemini_chat.send_message(safe_text, stream=True)

        def generate():
            for chunk in response:
                if chunk.text:
                    yield chunk.text

        return Response(generate(), mimetype='text/plain')

    except Exception as e:
        return jsonify({'response': f"API Error: {e}"})

# ==========================================
# ADMIN DASHBOARD
# ==========================================
@app.route('/admin')
def admin_dashboard():

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row

    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY id DESC")

    logs = c.fetchall()
    conn.close()

    return render_template('dashboard.html', logs=logs)

# ==========================================
# HELPER FUNCTION
# ==========================================
def save_and_respond(user_text, prediction, confidence, response_text, redirect_url):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute(
        "INSERT INTO logs (timestamp, user_input, prediction, confidence) VALUES (?, ?, ?, ?)",
        (timestamp, user_text, prediction, confidence)
    )

    conn.commit()
    conn.close()

    return jsonify({
        'prediction': prediction,
        'confidence': round(confidence, 4),
        'response': response_text,
        'redirect_url': redirect_url
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
