import os
import shutil
import hashlib
import secrets
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from api.db import DBConnection, init_db_connection, IS_POSTGRES
from api.resolve.resolver import get_dropdown_options, resolve_lookup
from api.pipeline.structure import ingest_document

app = FastAPI(title="BIS LIS Compliance Backend", version="2.4")

# Cryptographic password hashing helpers
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{dk.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, key_hex = hashed.split(":")
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return secrets.compare_digest(dk.hex(), key_hex)
    except Exception:
        return False

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LookupRequest(BaseModel):
    test_name: str
    is_number: Optional[str] = None
    wire_class: Optional[str] = None  # Mapping field name from class parameter
    size_mm2: Optional[float] = None
    material: Optional[str] = None
    category: Optional[str] = None
    hv_method: Optional[str] = None
    cable_diameter: Optional[str] = None
    component: Optional[str] = None
    timing: Optional[str] = None
    construction: Optional[str] = None
    core_type: Optional[str] = None
    hv_variant: Optional[str] = None
    cores_count: Optional[int] = None
    sheathing_status: Optional[str] = None
    conductor_grade: Optional[str] = None
    wire_diameter: Optional[float] = None

class AuthRequest(BaseModel):
    email: str
    password: str

@app.on_event("startup")
async def startup_event():
    await init_db_connection()
    async with DBConnection() as db:
        if IS_POSTGRES:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

@app.get("/api/options")
async def get_options():
    """
    Endpoint to retrieve dynamic dropdown options from the database.
    """
    async with DBConnection() as db:
        try:
            options = await get_dropdown_options(db)
            return options
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lookup")
async def execute_lookup(req: LookupRequest):
    """
    Endpoint to resolve a compliance standard lookup.
    """
    async with DBConnection() as db:
        try:
            # Map request model back to expected format in resolver
            payload = {
                "test_name": req.test_name,
                "is_number": req.is_number,
                "class": req.wire_class,
                "size_mm2": req.size_mm2,
                "material": req.material,
                "category": req.category,
                "hv_method": req.hv_method,
                "cable_diameter": req.cable_diameter,
                "component": req.component,
                "timing": req.timing,
                "construction": req.construction,
                "core_type": req.core_type,
                "hv_variant": req.hv_variant,
                "cores_count": req.cores_count,
                "sheathing_status": req.sheathing_status,
                "conductor_grade": req.conductor_grade,
                "wire_diameter": req.wire_diameter
            }
            result = await resolve_lookup(db, payload)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    is_number: str = Form(...),
    revision_label: str = Form(...),
    valid_from: Optional[str] = Form(None),
    valid_to: Optional[str] = Form(None)
):
    """
    Endpoint to upload and ingest a standard PDF document.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    # Temporary save uploaded file
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    async with DBConnection() as db:
        try:
            # 1. Run Docling PDF parser
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options.force_full_page_ocr = True
            
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            
            # Convert
            print(f"Parsing document {file.filename} using Docling...")
            result = converter.convert(temp_path)
            json_data = result.document.export_to_dict()
            
            # Setup document metadata
            doc_addr = f"{is_number.replace(' ', '')}-{revision_label}"
            metadata = {
                "is_number": is_number,
                "revision_label": revision_label,
                "document_address": doc_addr,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "is_current": True,
                "superseded_by": None
            }
            
            # 2. Invalidate previous current version of the same standard (Auto-update version)
            # Find any active matching standards
            prev_docs = await db.fetch("SELECT document_address FROM is_documents WHERE is_number = $1 AND is_current = TRUE", is_number)
            for prev in prev_docs:
                await db.execute("UPDATE is_documents SET is_current = FALSE, superseded_by = $1 WHERE document_address = $2", doc_addr, prev["document_address"])
                # Also purge cache entries pointing to old document versions
                await db.execute("DELETE FROM resolution_cache WHERE document_versions_used LIKE '%' || $1 || '%'", prev["document_address"])
                
            # 3. Ingest PDF contents (A1-A6 pipeline) using the unified async database runner
            await ingest_document(db, json_data, metadata)
                
            # Clean up temp file
            os.remove(temp_path)
            
            # Fetch summary metrics
            tables_count = await db.fetchval("SELECT count(*) FROM tables_meta WHERE document_address = $1", doc_addr)
            cells_count = await db.fetchval("SELECT count(*) FROM table_cells tc JOIN tables_meta tm ON tc.table_address = tm.table_address WHERE tm.document_address = $1", doc_addr)
            edges_count = await db.fetchval("SELECT count(*) FROM edges WHERE source_address LIKE '%' || $1 || '%'", doc_addr)
            
            return {
                "status": "success",
                "document_address": doc_addr,
                "summary": {
                    "tables_extracted": tables_count,
                    "cells_ingested": cells_count,
                    "edges_mapped": edges_count,
                    "superseded_versions": [p["document_address"] for p in prev_docs]
                }
            }
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/signup")
async def signup(req: AuthRequest):
    email = req.email.strip().lower()
    password = req.password
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
        
    async with DBConnection() as db:
        # Check if user exists
        existing = await db.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if existing:
            raise HTTPException(status_code=400, detail="email_exists")
            
        # Hash password and insert
        hashed = hash_password(password)
        await db.execute("INSERT INTO users (email, password_hash) VALUES ($1, $2)", email, hashed)
        
    return {"status": "success", "message": "User registered successfully."}

@app.post("/api/auth/login")
async def login(req: AuthRequest):
    email = req.email.strip().lower()
    password = req.password
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
        
    async with DBConnection() as db:
        user = await db.fetchrow("SELECT password_hash FROM users WHERE email = $1", email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
            
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
            
    return {"status": "success", "email": email}
