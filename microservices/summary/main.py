from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI(title="Summary Service", version="1.0.0")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

genai.configure(api_key=GEMINI_API_KEY)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-pro-latest')

class SummaryRequest(BaseModel):
    text: str
    max_length: int = 100

class SummaryResponse(BaseModel):
    original_text: str
    summary: str
    original_length: int
    summary_length: int

@app.get("/")
async def root():
    return {"service": "Summary Service", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/summarize", response_model=SummaryResponse)
async def summarize(request: SummaryRequest):
    try:
        prompt = f"""Summarize the following text in approximately {request.max_length} words.
Be concise and capture the main ideas.

Text: {request.text}

Summary:"""
        
        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        return {
            "original_text": request.text,
            "summary": summary,
            "original_length": len(request.text.split()),
            "summary_length": len(summary.split())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
