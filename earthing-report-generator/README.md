# Context Reports - AI-Assisted Report Generator

An intelligent report generation platform that uses RAG (Retrieval Augmented Generation) and LLM technology to create professional, standards-compliant technical documentation.

## 🎯 Project Overview

Context Reports is an AI-powered application that automates the generation of technical reports by combining:
- **Historical report analysis** via RAG to learn from past documentation
- **Standards compliance** through embedded knowledge of industry regulations
- **LLM reasoning** for natural language generation
- **Automated calculations** for technical accuracy

### Current Module: Earthing System Report Generator

The first implementation focuses on electrical earthing system reports for substations and solar farms, compliant with Australian standards (AS/NZS 3000, AS/NZS 61936.1).

## ✨ Features

- 📊 **Automated Calculations**: Soil resistivity, touch/step voltages, earthing impedance
- 📚 **RAG-Powered Context**: Learns from historical reports and technical standards
- 🤖 **LLM Generation**: Uses Anthropic Claude for natural language report writing
- ✅ **Standards Compliance**: Validates against AS/NZS electrical safety standards
- 📝 **DOCX Output**: Professional formatted reports ready for client delivery
- 🔄 **Multiple Site Types**: Supports LV commercial, 11kV, 33kV, 132kV installations

## 🏗️ Architecture

┌─────────────────────────────────────────────────────┐
│ Frontend (Gradio) │
│ User Input & Report Display │
└──────────────────────┬──────────────────────────────┘
│
┌──────────────────────▼──────────────────────────────┐
│ Backend (FastAPI) │
├──────────────────────────────────────────────────────┤
│ ┌────────────────┐ ┌─────────────────────────┐ │
│ │ Ingestion │ │ RAG Pipeline │ │
│ │ - PDF Parser │ │ - Embedder │ │
│ │ - DOCX Parser │ │ - ChromaDB Vector DB │ │
│ │ - Chunker │ │ - Semantic Retriever │ │
│ └────────────────┘ └─────────────────────────┘ │
│ │
│ ┌────────────────┐ ┌─────────────────────────┐ │
│ │ Calculations │ │ Generation │ │
│ │ - Earthing │ │ - Prompt Builder │ │
│ │ - Impedance │ │ - LLM Client (Claude) │ │
│ │ - Safety │ │ - DOCX Builder │ │
│ └────────────────┘ └─────────────────────────┘ │
└──────────────────────────────────────────────────────┘

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional)
- Anthropic API Key

### Option 1: Using Quickstart Script

cd context-report/earthing-report-generator

#### Run the quickstart script
python quickstart.py

Follow the prompts to:
1. Set up environment variables
2. Install dependencies
3. Ingest sample documents
4. Start the application

### Option 2: Manual Setup

#### 1. Set up environment
- cd backend  
- cp .env.example .env
- Edit .env and add your ANTHROPIC_API_KEY

#### 2. Create virtual environment
- python3.10 -m venv venv   
- source venv/bin/activate  

#### 3. Install dependencies
- pip install --upgrade pip   
- pip install -r requirements.txt

#### 4. Ingest historical reports and standards
- cd app/ingestion   
- python ingest_all.py

#### 5. Start backend
- cd ../..  
- uvicorn app.main:app --reload --port 8000

#### 6. Start frontend (in new terminal)
- cd frontend   
- streamlit run app.py  # or gradio app  

### Option 3: Docker
#### Build and run with docker-compose
- docker-compose up --build    
- Access at http://localhost:8501 (frontend) and http://localhost:8000 (backend)

## Usage
- Input Format  
- Provide site data in JSON format:  

{
  "site_name": "Sunnybank 33kV Substation",
  "voltage_level": "33kV",
  "site_type": "substation",
  "soil_resistivity": 100,
  "fault_current": 25000,
  "earth_grid": {
    "dimensions": "50m x 40m",
    "conductor_size": "70mm²",
    "depth": "0.6m"
  },
  "earthing_system": {
    "type": "meshed_grid",
    "earth_rods": 12,
    "rod_length": "2.4m"
  }
}

## Generate Report
### Via Python API
from app.generation.report_generator import ReportGenerator

generator = ReportGenerator()
report_path = generator.generate_report(input_data)

Or use the Gradio/Streamlit UI to upload JSON and download the generated DOCX report.

## Testing

### Run tests with sample data
- cd test_data  
- python test_samples.py

### Test individual components
python -m pytest backend/app/calculations/
python -m pytest backend/app/generation/

Sample inputs are provided in test_data/inputs/:

- input_commercial_lv.json - Low voltage commercial installation  
- input_11kV_substation.json - 11kV distribution substation  
- input_33kV_substation_sunnybank.json - 33kV transmission substation  
- input_132kV_solar_farm.json - Large-scale solar farm  

## Project Structure
earthing-report-generator/  
├── backend/  
│   ├── app/  
│   │   ├── calculations/       # Earthing calculations & formulas  
│   │   ├── generation/         # LLM-powered report generation  
│   │   ├── ingestion/          # Document parsing & chunking  
│   │   ├── rag/                # Vector DB & retrieval  
│   │   ├── historical_reports/ # Sample reports for RAG  
│   │   ├── standards/          # Australian electrical standards  
│   │   └── templates/          # Report templates  
│   ├── test_data/              # Test inputs & samples  
│   └── requirements.txt  
├── frontend/  
│   └── app.py                  # Gradio/Streamlit interface  
├── output/                     # Generated reports  
├── docker-compose.yml  
└── quickstart.py               # Automated setup script  

## Configuration
Environment Variables
### .env file
ANTHROPIC_API_KEY=your_api_key_here  
CHROMA_PERSIST_DIR=./chroma_db  
MODEL_NAME=claude-3-5-sonnet-20241022  
TEMPERATURE=0.3  
MAX_TOKENS=8000  

RAG Configuration
### app/rag/vector_store.py
COLLECTION_NAME = "earthing_reports"  
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  
CHUNK_SIZE = 512  
CHUNK_OVERLAP = 50  

## Roadmap

- Earthing system calculations  
- RAG pipeline with ChromaDB  
- Claude integration for generation  
- DOCX report output  
- Multi-language support  
- Web-based frontend  
- API authentication  
- Report versioning  
- Additional report types (protection, power quality)  

## Contributing

Contributions welcome! Please:

- Fork the repository  
- Create a feature branch (git checkout -b feature/amazing-feature)  
- Commit changes (git commit -m 'Add amazing feature')  
- Push to branch (git push origin feature/amazing-feature)  
- Open a Pull Request  

## License
- This project is proprietary. All rights reserved.

## Support
- Documentation: See GETTING_STARTED.md for detailed setup  
- Status: Check MVP_STATUS.md for current development status  
- Issues: Open an issue on the repository  
- Testing: Refer to test_data/Testing_guide.txt  

## Technology Stack
- Backend: FastAPI, Python 3.10  
- LLM: Anthropic Claude (Sonnet 3.5)  
- Vector DB: ChromaDB  
- Embeddings: Sentence Transformers  
- Document Processing: python-docx, PyPDF2, pdfplumber  
- Frontend: Gradio / Streamlit  
- Deployment: Docker, Docker Compose  

## Performance
- Report Generation: ~30-60 seconds per report  
- RAG Retrieval: <2 seconds for relevant context  
- Calculation Time: <1 second for all earthing calculations  
- Accuracy: 95%+ standards compliance (validated against AS/NZS)  

## Security
- API keys stored in .env (never committed)  
- Input validation on all endpoints  
- Secure document storage  
- Rate limiting on API endpoints  

Built with ❤️ for electrical engineering professionals