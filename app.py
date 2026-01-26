import os
import io
import base64
import ssl
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai

# SSL Settings
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Saita API da Model
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# MODEL DIN DA YA YI AIKI
MODEL_NAME = 'gemini-flash-latest' 
model = genai.GenerativeModel(model_name=MODEL_NAME)

app = Flask(__name__)
CORS(app)

# SYSTEM PROMPT - AN GYARA DON KAYATARWA BA TARE DA MARKDOWN BA
SYSTEM_PROMPT = """LafiyaAI. Kai kwararren likitan AI ne mai ilimin gaggawa da binciken lafiya.
Aikin ka shi ne taimaka wa mai amfani fahimtar yanayin lafiyarsa cikin harshen Hausa na Najeriya mai sauki.

DOKOKIN KA (TSARIN RUBUTU):
1. KADA KA YI AMFANI DA MARKDOWN (kamar ##, **, __). 
2. Maimakon ##, yi amfani da Emojis kamar 🏥, 🩺, 🧪 ko 💊 don manyan jigogi.
3. Maimakon **, yi amfani da manyan haruffa (CAPITAL LETTERS) don nuna muhimmanci.
4. Yi amfani da dash (-) ko digobi (•) don lissafa abubuwa.
5. Idan aka turo hoto kawai, bincika hoton nan take ka fadi abin da ka gani da shawarar abin da za a yi.
6. Idan murya (audio) aka turo, saurara ka ba da amsa kai tsaye.
7. Kada ka cika yawan tambayoyi; ba da mafita nan take cikin ladabi da girmamawa.
8. Idan yanayin gaggawa ne, bada matakan farko (First Aid) sannan ka bukaci su ga likita da gaggawa.
9. Koda yaushe tuna musu tuntuibar likita a karshen magana. ✅"""

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="ha">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LafiyaAI - Likitan Zamani</title>
        <style>
            :root { --primary: #008080; --secondary: #004d40; --bg: #f0fdfa; }
            body { 
                font-family: 'Segoe UI', sans-serif; 
                background: radial-gradient(circle at center, #f0fdfa, #b2dfdb);
                min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; 
            }
            .card { 
                background: white; padding: 40px; border-radius: 30px; 
                box-shadow: 0 20px 50px rgba(0,128,128,0.15); text-align: center; 
                max-width: 480px; width: 90%; animation: slideUp 0.6s ease-out;
            }
            @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
            .logo-box { 
                width: 80px; height: 80px; background: var(--primary); border-radius: 20px; 
                margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; 
                position: relative; box-shadow: 0 10px 20px rgba(0,128,128,0.2);
            }
            .cross-v { width: 12px; height: 40px; background: white; border-radius: 5px; position: absolute; }
            .cross-h { width: 40px; height: 12px; background: white; border-radius: 5px; position: absolute; }
            h2 { color: var(--secondary); margin-bottom: 5px; font-size: 28px; }
            .subtitle { color: #666; font-size: 15px; margin-bottom: 30px; }
            .input-group { text-align: left; margin-bottom: 20px; }
            input[type="text"] { 
                width: 100%; padding: 15px; border: 2px solid #e0f2f1; border-radius: 12px; 
                box-sizing: border-box; font-size: 16px;
            }
            button { 
                width: 100%; padding: 18px; background: var(--primary); color: white; border: none; 
                border-radius: 15px; font-size: 17px; font-weight: bold; cursor: pointer; transition: 0.3s;
            }
            button:hover { background: var(--secondary); transform: scale(1.02); }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="logo-box"><div class="cross-v"></div><div class="cross-h"></div></div>
            <h2>LafiyaAI</h2>
            <p class="subtitle">Abokin Tattaunawar Lafiyarka ta AI</p>
            <form action="/diagnose" method="post" enctype="multipart/form-data">
                <div class="input-group">
                    <input type="text" name="description" placeholder="Bayyana yadda kake ji..." required>
                </div>
                <button type="submit">Fara Binciken Lafiya</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/diagnose', methods=['POST'])
def diagnose():
    try:
        user_text = ""
        user_file = None
        is_json = False

        # KARBAR BAYANI DAGA MOBILE APP (JSON)
        if request.is_json:
            is_json = True
            data = request.get_json()
            user_text = data.get('description') or data.get('message') or ""
            file_b64 = data.get('file_data')
            file_type = data.get('file_type')

            if file_b64:
                if file_type == 'image':
                    img_data = base64.b64decode(file_b64)
                    user_file = Image.open(io.BytesIO(img_data))
                elif file_type == 'audio':
                    # Don murya
                    user_file = {"mime_type": "audio/mp4", "data": file_b64}
        
        # KARBAR BAYANI DAGA WEB BROWSER (Form)
        else:
            user_text = request.form.get('description') or request.form.get('message') or ""
            file = request.files.get('image')
            if file and file.filename != '':
                user_file = Image.open(io.BytesIO(file.read()))

        # Tabbatar da an turo akalla abu daya
        if not user_text and not user_file:
            return jsonify({"result": "Don Allah shigar da bayani, hoto, ko murya don bincike. ⚠️"}), 400

        # AIKIN GEMINI
        contents = [SYSTEM_PROMPT]
        
        if user_file:
            contents.append(user_file)
            
        if user_text:
            contents.append(f"Bayani/Tambaya daga mai amfani: {user_text}")
        elif user_file and not user_text:
            # Idan hoto ne kawai ba tare da rubutu ba
            contents.append("MAI AMFANI YA TURO WANNAN FAYIL DIN KAWAI. Duba shi daki-daki ka ba da bayani cikin Hausa.")

        response = model.generate_content(contents)
        ai_message = response.text

        # MAYAR DA AMSA
        if is_json:
            return jsonify({"result": ai_message})
        else:
            safe_message = ai_message.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; background: #f0fdfa; margin:0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
                    .container {{ background: white; padding: 30px; border-radius: 25px; box-shadow: 0 15px 40px rgba(0,0,0,0.1); max-width: 700px; width: 95%; }}
                    h3 {{ color: #008080; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }}
                    #result {{ line-height: 1.6; color: #333; font-size: 16px; text-align: left; white-space: pre-wrap; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h3>Sakamakon Bincike:</h3>
                    <div id="result">{ai_message}</div>
                    <div class="btn-back" style="text-align: center; margin-top: 20px;">
                        <a href="/" style="text-decoration: none; background: #008080; color: white; padding: 10px 20px; border-radius: 10px;">Koma Baya</a>
                    </div>
                </div>
            </body>
            </html>
            '''
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"result": f"An samu kuskure: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)