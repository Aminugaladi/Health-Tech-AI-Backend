import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- Ga jerin dukkan Models din da suke asusunka ---")
try:
    # Kawai mu buga sunan kowane model ba tare da sharadi ba
    for m in client.models.list():
        print(f"Model: {m.name}")
except Exception as e:
    print(f"An samu matsala: {e}")