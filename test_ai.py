import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    # Gwada kiran 2.5-flash kamar yadda kace
    model = genai.GenerativeModel('gemini-2.0-flash-exp') # Ko 'gemini-2.5-flash' idan tabbas shi ne
    response = model.generate_content("Sannu!")
    print("AI TA CE: ", response.text)
except Exception as e:
    print("HAR YANZU BAI YI BA: ", e)
    
    # Idan bai yi ba, bari mu lissafa dukkan models din da suke aiki a API Key dinka
    print("\nGa jerin Models din da suke aiki a Key dinka:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)