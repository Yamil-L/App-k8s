from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI(title="Keywords Service", version="1.0.0")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

genai.configure(api_key=GEMINI_API_KEY)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-pro-latest')

class KeywordsRequest(BaseModel):
    text: str
    max_keywords: int = 10

class KeywordsResponse(BaseModel):
    text: str
    keywords: list
    relevance_scores: dict

@app.get("/")
async def root():
    return {"service": "Keywords Service", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/extract", response_model=KeywordsResponse)
async def extract_keywords(request: KeywordsRequest):
    try:
        prompt = f"""Extract the top {request.max_keywords} most important keywords from this text.
List them in order of relevance, one per line.
Only provide the keywords, no explanations.

Text: {request.text}

Keywords:"""
        
        response = model.generate_content(prompt)
        keywords_text = response.text.strip()
        
        # Parse keywords
        keywords = []
        for line in keywords_text.split('\n'):
            clean_line = line.strip().lstrip('1234567890.-•* ').strip()
            if clean_line and len(clean_line) > 2:
                keywords.append(clean_line)
        
        keywords = keywords[:request.max_keywords]
        
        # Generate mock relevance scores
        relevance_scores = {kw: round(1.0 - (i * 0.1), 2) for i, kw in enumerate(keywords)}
        
        return {
            "text": request.text,
            "keywords": keywords,
            "relevance_scores": relevance_scores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keywords extraction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
