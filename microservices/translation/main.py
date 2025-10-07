from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI(title="Translation Service", version="1.0.0")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

genai.configure(api_key=GEMINI_API_KEY)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-pro-latest')

class TranslationRequest(BaseModel):
    text: str
    target_language: str = "es"

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str

@app.get("/")
async def root():
    return {"service": "Translation Service", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest):
    try:
        prompt = f"""Translate the following text to {request.target_language}. 
Only provide the translation, no explanations.

Text: {request.text}

Translation:"""
        
        response = model.generate_content(prompt)
        translated_text = response.text.strip()
        
        return {
            "original_text": request.text,
            "translated_text": translated_text,
            "source_language": "auto",
            "target_language": request.target_language
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
