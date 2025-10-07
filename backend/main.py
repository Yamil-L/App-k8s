from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import httpx
import asyncio
import traceback
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Text Processor API Gateway", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de base de datos
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "textprocessor"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "supersecret123")
}

# URLs de microservicios
SERVICES = {
    "translate": "http://translation:8001",
    "summary": "http://summary:8002",
    "analytics": "http://analytics:8003",
    "improve": "http://improve:8004",
    "keywords": "http://keywords:8005"
}

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

class TextRequest(BaseModel):
    text: str
    service: str
    options: Optional[dict] = {}

class TextResponse(BaseModel):
    id: int
    original_text: str
    processed_text: str
    service_used: str
    status: str

class HealthResponse(BaseModel):
    status: str
    database: str
    version: str
    microservices: dict

@app.on_event("startup")
async def startup_event():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS text_requests (
                    id SERIAL PRIMARY KEY,
                    original_text TEXT NOT NULL,
                    processed_text TEXT,
                    service_used VARCHAR(50) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_service_used 
                ON text_requests(service_used)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON text_requests(created_at DESC)
            """)

@app.get("/")
async def root():
    return {
        "message": "Text Processor API Gateway",
        "version": "2.0.0",
        "microservices": list(SERVICES.keys()),
        "endpoints": {
            "health": "/health",
            "process": "/api/process",
            "history": "/api/history",
            "stats": "/api/stats"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    db_status = "disconnected"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check microservices
    microservices_status = {}
    async with httpx.AsyncClient(timeout=2.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/health")
                microservices_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception as e:
                microservices_status[service_name] = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "version": "2.0.0",
        "microservices": microservices_status
    }

@app.post("/api/process", response_model=TextResponse)
async def process_text(request: TextRequest):
    try:
        logger.info(f"Processing request - service: {request.service}, text length: {len(request.text)}")
        
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if request.service not in SERVICES:
            raise HTTPException(status_code=400, detail=f"Invalid service. Available: {list(SERVICES.keys())}")
        
        service_url = SERVICES[request.service]
        logger.info(f"Calling service at: {service_url}")
        
        processed_text = ""
        metadata = ""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if request.service == "translate":
                target_lang = request.options.get("target_language", "es")
                logger.info(f"Translating to: {target_lang}")
                
                response = await client.post(
                    f"{service_url}/translate",
                    json={"text": request.text, "target_language": target_lang}
                )
                logger.info(f"Translation service responded with status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    processed_text = data.get("translated_text", "")
                    metadata = str(data)
                else:
                    error_text = response.text
                    logger.error(f"Translation service error: {error_text}")
                    raise HTTPException(status_code=response.status_code, detail=f"Translation service error: {error_text}")
                    
            elif request.service == "summary":
                max_length = request.options.get("max_length", 100)
                response = await client.post(
                    f"{service_url}/summarize",
                    json={"text": request.text, "max_length": max_length}
                )
                if response.status_code == 200:
                    data = response.json()
                    processed_text = data.get("summary", "")
                    metadata = str(data)
                else:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                    
            elif request.service == "analytics":
                response = await client.post(
                    f"{service_url}/analyze",
                    json={"text": request.text}
                )
                if response.status_code == 200:
                    data = response.json()
                    processed_text = f"Sentiment: {data.get('sentiment', 'N/A')}\n"
                    processed_text += f"Entities: {', '.join(data.get('entities', []))}\n"
                    processed_text += f"Topics: {', '.join(data.get('topics', []))}\n"
                    processed_text += f"Complexity: {data.get('complexity', 'N/A')}\n"
                    processed_text += f"Word count: {data.get('word_count', 0)}"
                    metadata = str(data)
                else:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                    
            elif request.service == "improve":
                style = request.options.get("style", "professional")
                response = await client.post(
                    f"{service_url}/improve",
                    json={"text": request.text, "style": style}
                )
                if response.status_code == 200:
                    data = response.json()
                    processed_text = data.get("improved_text", "")
                    metadata = str(data)
                else:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                    
            elif request.service == "keywords":
                max_keywords = request.options.get("max_keywords", 10)
                response = await client.post(
                    f"{service_url}/extract",
                    json={"text": request.text, "max_keywords": max_keywords}
                )
                if response.status_code == 200:
                    data = response.json()
                    keywords = data.get("keywords", [])
                    processed_text = "Keywords: " + ", ".join(keywords)
                    metadata = str(data)
                else:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
            
            if not processed_text:
                raise HTTPException(status_code=500, detail="Microservice returned empty response")
        
        logger.info("Successfully processed text, saving to database")
        
        # Save to database
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO text_requests (original_text, processed_text, service_used, status, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, original_text, processed_text, service_used, status
                """, (request.text, processed_text, request.service, "completed", metadata))
                
                result = cur.fetchone()
        
        logger.info(f"Request saved with ID: {result['id']}")
        return result
        
    except HTTPException:
        raise
    except httpx.TimeoutException as e:
        logger.error(f"Timeout error: {str(e)}")
        raise HTTPException(status_code=504, detail=f"Timeout calling {request.service} service")
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=503, detail=f"Error calling {request.service} service: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/api/history", response_model=List[TextResponse])
async def get_history(limit: int = 10):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, original_text, processed_text, service_used, status
                FROM text_requests
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            results = cur.fetchall()
    
    return results

@app.get("/api/stats")
async def get_stats():
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    service_used,
                    COUNT(*) as count,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as errors
                FROM text_requests
                GROUP BY service_used
                ORDER BY count DESC
            """)
            
            stats = cur.fetchall()
            
            cur.execute("SELECT COUNT(*) as total FROM text_requests")
            total = cur.fetchone()
    
    return {
        "total_requests": total["total"],
        "by_service": stats
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
