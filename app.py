import os
import io
import base64
import ssl
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Magance Matsalar SSL
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# 2. Saita API da Model
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Muna amfani da wannan sunan tunda shi ne yake a jerin da kake da shi
MODEL_NAME = 'models/gemini-1.5-flash-latest' 
model = genai.GenerativeModel(model_name=MODEL_NAME)

app = Flask(__name__)
CORS(app)

SYSTEM_PROMPT = "Sunanka LafiyaAI. Kai kwararren likitan AI ne. Yi magana da Hausa kawai cikin girmamawa da lallashi."

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
            <form action="/diagnose" method="post">
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
        file_type = None
        is_json = False

        # 1. KARBAR BAYANI DAGA MOBILE APP (JSON)
        if request.is_json:
            is_json = True
            data = request.get_json()
            user_text = data.get('description', '')
            file_b64 = data.get('file_data')
            file_type = data.get('file_type')

            if file_b64:
                if file_type == 'image':
                    img_data = base64.b64decode(file_b64)
                    user_file = Image.open(io.BytesIO(img_data))
                elif file_type == 'audio':
                    user_file = {"mime_type": "audio/m4a", "data": file_b64}
        
        # 2. KARBAR BAYANI DAGA WEB BROWSER (Form)
        else:
            user_text = request.form.get('description', '')
            file = request.files.get('image')
            if file and file.filename != '':
                user_file = Image.open(io.BytesIO(file.read()))
                file_type = 'image'

        if not user_text and not user_file:
            return jsonify({"error": "Babu bayani"}), 400

        # 3. AIKIN GEMINI
        contents = [SYSTEM_PROMPT]
        if user_text: contents.append(f"Korafi: {user_text}")
        if user_file: contents.append(user_file)

        response = model.generate_content(contents)
        ai_message = response.text

        # 4. MAYAR DA AMSA
        if is_json:
            return jsonify({"result": ai_message})
        else:
            # Gyara rubutu don JavaScript ya iya karanta shi ba tare da kuskure ba
            safe_message = ai_message.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; background: #f0fdfa; margin:0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
                    .container {{ background: white; padding: 30px; border-radius: 25px; box-shadow: 0 15px 40px rgba(0,128,128,0.15); max-width: 700px; width: 95%; }}
                    h3 {{ color: #008080; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }}
                    #result {{ line-height: 1.6; color: #333; font-size: 16px; text-align: left; }}
                    #result h1, #result h2, #result h3 {{ color: #004d40; margin-top: 20px; }}
                    #result ul, #result ol {{ padding-left: 20px; }}
                    #result li {{ margin-bottom: 8px; }}
                    .btn-back {{ text-align: center; margin-top: 30px; }}
                    .btn-back a {{ text-decoration: none; background: #008080; color: white; padding: 12px 25px; border-radius: 10px; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h3>Sakamakon Bincike:</h3>
                    <div id="result"></div>
                    <div class="btn-back">
                        <a href="/">Koma Baya</a>
                    </div>
                </div>
                <script>
                    const rawMessage = `{safe_message}`;
                    document.getElementById('result').innerHTML = marked.parse(rawMessage);
                </script>
            </body>
            </html>
            '''
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)