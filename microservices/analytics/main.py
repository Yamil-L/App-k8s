from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI(title="Analytics Service", version="1.0.0")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

genai.configure(api_key=GEMINI_API_KEY)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-pro-latest')

class AnalyticsRequest(BaseModel):
    text: str

class AnalyticsResponse(BaseModel):
    text: str
    sentiment: str
    entities: list
    topics: list
    word_count: int
    sentence_count: int
    complexity: str

@app.get("/")
async def root():
    return {"service": "Analytics Service", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/analyze", response_model=AnalyticsResponse)
async def analyze(request: AnalyticsRequest):
    try:
        prompt = f"""Analyze the following text and provide:
1. Sentiment (positive/negative/neutral)
2. Main entities (people, places, organizations)
3. Main topics
4. Complexity level (simple/medium/complex)

Respond in JSON format:
{{
    "sentiment": "...",
    "entities": ["...", "..."],
    "topics": ["...", "..."],
    "complexity": "..."
}}

Text: {request.text}"""
        
        response = model.generate_content(prompt)
        
        # Parse basic JSON from response
        import json
        try:
            analysis = json.loads(response.text.strip())
        except:
            # Fallback if JSON parsing fails
            analysis = {
                "sentiment": "neutral",
                "entities": [],
                "topics": ["general"],
                "complexity": "medium"
            }
        
        word_count = len(request.text.split())
        sentence_count = request.text.count('.') + request.text.count('!') + request.text.count('?')
        
        return {
            "text": request.text,
            "sentiment": analysis.get("sentiment", "neutral"),
            "entities": analysis.get("entities", []),
            "topics": analysis.get("topics", []),
            "word_count": word_count,
            "sentence_count": max(sentence_count, 1),
            "complexity": analysis.get("complexity", "medium")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
