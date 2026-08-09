import os
import io
import sys
import json
import logging
import pandas as pd
from typing import Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure root directory is in sys.path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.data_processing import process_social_media_file
    from services.analysis_aggregator import aggregate_social_media_data
    from services.report_generator import generate_management_report
except ImportError as e:
    logging.error(f"Failed to import services: {e}")
    # Fallback or error handling if services are missing in specific environments

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".json"}

# --- FastAPI App ---
app = FastAPI(
    title="Socia. Analytics API",
    description="Advanced AI-powered social media data analysis.",
    version="2.0.0"
)

# Enable CORS for frontend communication (restricted to configured origins)
_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
]
_cors_env = os.getenv("CORS_ORIGINS", "").strip()
allow_origins = (
    [o.strip() for o in _cors_env.split(",") if o.strip()] if _cors_env else _DEFAULT_CORS_ORIGINS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---

def validate_upload(file: UploadFile):
    """Checks file extension."""
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

def _json_to_dataframe(content: bytes) -> pd.DataFrame:
    """
    Converts JSON uploads to a DataFrame, handling both the documented
    schema format ({'platform': ..., 'posts': [...]}) and raw JSON arrays.

    pd.read_json chokes on the schema format because it mixes a scalar
    ('platform') with a list of records ('posts'), producing the pandas
    'Mixing dicts with non-Series' error (or silently mis-parsing on
    newer pandas versions).
    """
    raw = json.loads(content.decode("utf-8"))
    if isinstance(raw, dict):
        for key in ("posts", "data", "items", "tweets"):
            records = raw.get(key)
            if isinstance(records, list) and records:
                if all(isinstance(r, dict) for r in records):
                    return pd.DataFrame(records)
    return pd.read_json(io.BytesIO(content))

async def run_analysis_pipeline(file: UploadFile) -> Dict[str, Any]:
    """
    Standardizes the flow:
    1. Save temporarily or read into memory
    2. Process and clean text
    3. Aggregate sentiment and topics
    4. Generate management report
    """
    try:
        # Load into DataFrame (existing logic adapted)
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds the maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB."
            )
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext == '.csv':
            df = pd.read_csv(io.BytesIO(content))
        elif file_ext == '.xlsx':
            df = pd.read_excel(io.BytesIO(content))
        elif file_ext == '.json':
            df = _json_to_dataframe(content)
        else:
            raise ValueError("Unsupported file type during processing.")

        # Basic cleaning: ensure standard columns
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        
        # We need text data. Look for a 'text' or 'content' or 'tweet_text' column.
        possible_text_cols = ['text', 'content', 'tweet_text', 'message', 'body']
        text_col = next((c for c in df.columns if c in possible_text_cols), None)
        
        if not text_col:
            # Fallback: find the first object/string column with longest average length
            str_cols = df.select_dtypes(include=['object', 'string']).columns
            if not str_cols.empty:
                text_col = str_cols[0]
            else:
                raise HTTPException(status_code=400, detail="No readable text column found in the file.")

        texts = df[text_col].dropna().astype(str).tolist()
        
        if not texts:
            raise HTTPException(status_code=400, detail="No text entries found in the file.")

        # Run Core Services (Async)
        logger.info(f"Analyzing {len(texts)} entries from {file.filename}")
        
        # 1. Aggregate sentiment and topics
        aggregated_data = await aggregate_social_media_data(texts, max_concurrent=5)
        
        if "error" in aggregated_data:
            raise HTTPException(status_code=500, detail=aggregated_data["error"])

        # 2. Generate final markdown report
        report_markdown = await generate_management_report(aggregated_data)

        return {
            "status": "success",
            "filename": file.filename,
            "total_rows": len(df),
            "analysis": aggregated_data,
            "report_markdown": report_markdown
        }

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# --- Endpoints ---

@app.get("/")
async def root():
    return {"message": "Socia. API is live"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Entry point for file analysis."""
    # 1. Validate
    validate_upload(file)
    
    # 2. Execute full pipeline
    result = await run_analysis_pipeline(file)
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
