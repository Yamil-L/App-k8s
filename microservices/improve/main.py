from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI(title="Improve Service", version="1.0.0")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

genai.configure(api_key=GEMINI_API_KEY)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-pro-latest')

class ImproveRequest(BaseModel):
    text: str
    style: str = "professional"  # professional, casual, academic

class ImproveResponse(BaseModel):
    original_text: str
    improved_text: str
    suggestions: list
    style: str

@app.get("/")
async def root():
    return {"service": "Improve Service", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/improve", response_model=ImproveResponse)
async def improve(request: ImproveRequest):
    try:
        prompt = f"""Improve the following text with a {request.style} style.
Fix grammar, improve clarity, and enhance readability.
Provide the improved version and 3 key suggestions.

Format your response as:
IMPROVED TEXT:
[improved version here]

SUGGESTIONS:
1. [suggestion 1]
2. [suggestion 2]
3. [suggestion 3]

Original text: {request.text}"""
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Parse response
        parts = result.split("SUGGESTIONS:")
        improved_text = parts[0].replace("IMPROVED TEXT:", "").strip()
        
        suggestions = []
        if len(parts) > 1:
            suggestions_text = parts[1].strip()
            suggestions = [s.strip() for s in suggestions_text.split("\n") if s.strip() and any(c.isalnum() for c in s)][:3]
        
        if not suggestions:
            suggestions = ["Text has been improved for clarity", "Grammar checked", "Style enhanced"]
        
        return {
            "original_text": request.text,
            "improved_text": improved_text,
            "suggestions": suggestions,
            "style": request.style
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Improve error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
