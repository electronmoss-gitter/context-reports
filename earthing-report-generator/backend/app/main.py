"""
Main FastAPI application for Earthing Report Generator MVP
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from pathlib import Path
import json

from app.ingestion.ingest_all import ingest_documents
from app.generation.report_generator import ReportGenerator
from app.rag.retriever import Retriever

app = FastAPI(
    title="Earthing Report Generator API",
    description="AI-powered electrical earthing study report generation",
    version="0.1.0"
)

# Initialize components
retriever = Retriever()
report_generator = ReportGenerator(retriever)

# Data models
class ProjectData(BaseModel):
    """Input data for generating an earthing study report"""
    # Project information
    project_name: str
    client_name: str
    site_address: str
    project_number: str
    engineer_name: str
    
    # Electrical system data
    voltage_level: str  # e.g., "11kV", "33kV", "132kV"
    fault_current_symmetrical: float  # kA
    fault_current_asymmetrical: Optional[float] = None  # kA
    fault_clearance_time: float  # seconds
    transformer_rating: Optional[str] = None  # e.g., "20MVA"
    
    # Site characteristics
    soil_resistivity_measurements: List[Dict[str, float]]  # [{depth: m, resistivity: ohm_m}]
    soil_model_type: str = "two_layer"  # "uniform", "two_layer", "multi_layer"
    site_length: Optional[float] = None  # meters
    site_width: Optional[float] = None  # meters
    
    # Design requirements
    target_grid_resistance: float  # ohms
    touch_potential_limit: Optional[float] = None  # volts (auto-calculated if not provided)
    step_potential_limit: Optional[float] = None  # volts
    earth_conductor_size: Optional[str] = None  # e.g., "70mm2"
    
    # Additional data
    project_type: str = "substation"  # "substation", "solar_farm", "commercial", "industrial"
    special_requirements: Optional[str] = None

class ReportGenerationRequest(BaseModel):
    """Request to generate a report"""
    project_data: ProjectData
    template_name: str = "standard"
    include_appendices: bool = True
    calculation_methods: List[str] = ["schwarz", "ieee80"]

class ReportGenerationResponse(BaseModel):
    """Response after generating a report"""
    success: bool
    report_id: str
    report_path: str
    quality_score: float
    warnings: List[str] = []
    generation_time_seconds: float

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Earthing Report Generator API",
        "version": "0.1.0"
    }

@app.post("/api/v1/ingest")
async def ingest_historical_reports():
    """
    Ingest all historical reports from data/historical_reports directory
    This processes PDFs/DOCX, chunks them, creates embeddings, and stores in vector DB
    """
    try:
        result = ingest_documents()
        return {
            "success": True,
            "message": "Documents ingested successfully",
            "documents_processed": result["documents_processed"],
            "chunks_created": result["chunks_created"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/api/v1/upload-report")
async def upload_report(file: UploadFile = File(...)):
    """
    Upload a single historical report for ingestion
    """
    # Save uploaded file
    upload_path = Path("data/historical_reports") / file.filename
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Ingest the single document
    try:
        result = ingest_documents(specific_file=str(upload_path))
        return {
            "success": True,
            "message": f"Report '{file.filename}' uploaded and ingested",
            "chunks_created": result["chunks_created"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/v1/validate-input", response_model=Dict[str, Any])
async def validate_input_data(project_data: ProjectData):
    """
    Validate input data before report generation
    Returns validation results with errors/warnings
    """
    from app.generation.validator import InputValidator
    
    validator = InputValidator()
    validation_result = validator.validate(project_data.dict())
    
    return validation_result

@app.post("/api/v1/generate-report", response_model=ReportGenerationResponse)
async def generate_report(request: ReportGenerationRequest):
    """
    Generate an earthing study report based on input data
    """
    import time
    start_time = time.time()
    
    try:
        # Validate input first
        from app.generation.validator import InputValidator
        validator = InputValidator()
        validation = validator.validate(request.project_data.dict())
        
        if validation["validation_status"] == "fail":
            raise HTTPException(
                status_code=400,
                detail=f"Input validation failed: {validation['errors']}"
            )
        
        # Generate report
        result = report_generator.generate(
            project_data=request.project_data.dict(),
            template_name=request.template_name,
            include_appendices=request.include_appendices,
            calculation_methods=request.calculation_methods
        )
        
        generation_time = time.time() - start_time
        
        return ReportGenerationResponse(
            success=True,
            report_id=result["report_id"],
            report_path=result["output_path"],
            quality_score=result["quality_score"],
            warnings=validation.get("warnings", []),
            generation_time_seconds=generation_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@app.get("/api/v1/download-report/{report_id}")
async def download_report(report_id: str):
    """
    Download a generated report by ID
    """
    output_dir = Path(os.getenv("OUTPUT_PATH", "../output/generated_reports"))
    report_path = output_dir / f"{report_id}.docx"
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=str(report_path),
        filename=f"earthing_study_{report_id}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.get("/api/v1/stats")
async def get_statistics():
    """
    Get system statistics (documents ingested, reports generated, etc.)
    """
    vector_db_path = Path(os.getenv("VECTOR_DB_PATH", "./data/vector_db"))
    reports_path = Path(os.getenv("OUTPUT_PATH", "../output/generated_reports"))
    historical_reports_path = Path(os.getenv("HISTORICAL_REPORTS_PATH", "./data/historical_reports"))
    
    return {
        "historical_reports_count": len(list(historical_reports_path.glob("*.pdf"))) + 
                                   len(list(historical_reports_path.glob("*.docx"))),
        "generated_reports_count": len(list(reports_path.glob("*.docx"))),
        "vector_db_exists": vector_db_path.exists(),
        "retriever_ready": retriever.is_ready()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)