from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import uvicorn

from backend import models, schemas, database, ai_service

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Motor Insurance Claim Verification API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def save_claim_task(filename: str, result: schemas.ClaimResult):
    """Background task to save claim result to database"""
    db = database.SessionLocal()
    try:
        db_claim = models.Claim(
            filename=filename,
            status=result.status,
            extracted_details=result.extracted_details
        )
        db.add(db_claim)
        db.commit()
    finally:
        db.close()

@app.post("/upload-claims/")
async def upload_claims(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    responses = []
    
    for file in files:
        # Validate file type
        if not file.content_type.startswith("image/") and file.content_type != "application/pdf":
            responses.append({
                "filename": file.filename,
                "status": "rejected",
                "reason": f"Unsupported file type: {file.content_type}. Only images and PDFs are allowed."
            })
            continue
            
        try:
            content = await file.read()
            
            # Process with Gemini API
            result = await ai_service.process_claim_document(content, file.content_type)
            
            # Save mapping to database in the background
            background_tasks.add_task(save_claim_task, file.filename, result)
            
            responses.append({
                "filename": file.filename,
                "status": result.status,
                "extracted_details": result.extracted_details,
                "missing_fields": result.missing_fields
            })
            
        except Exception as e:
            responses.append({
                "filename": file.filename,
                "status": "rejected",
                "reason": f"Error processing file: {str(e)}"
            })

    return {"results": responses}

@app.get("/api/claims/")
async def get_all_claims(db: Session = Depends(database.get_db)):
    claims = db.query(models.Claim).order_by(desc(models.Claim.timestamp)).all()
    return {"results": claims}
