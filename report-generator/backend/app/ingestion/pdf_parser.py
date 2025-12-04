"""
PDF Parser - Extract text and metadata from PDF earthing study reports
"""
import PyPDF2
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional
import re

class PDFParser:
    """Parse PDF documents and extract structured content"""
    
    def __init__(self):
        self.section_patterns = {
            "executive_summary": r"(?i)(executive\s+summary|summary)",
            "site_description": r"(?i)(site\s+description|project\s+description|location)",
            "methodology": r"(?i)(methodology|method|approach|standards)",
            "soil_resistivity": r"(?i)(soil\s+resistivity|soil\s+test|wenner)",
            "earthing_design": r"(?i)(earthing\s+(system\s+)?design|grid\s+design|earth\s+electrode)",
            "calculations": r"(?i)(calculations?|analysis|design\s+calculations)",
            "touch_step": r"(?i)(touch\s+(and\s+)?step\s+potential|safety\s+analysis)",
            "compliance": r"(?i)(compliance|standards?\s+compliance|conformance)",
            "recommendations": r"(?i)(recommendations?|conclusions?)"
        }
    
    def parse(self, pdf_path: str) -> Dict:
        """
        Parse a PDF document and extract text with metadata
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict with extracted text, sections, and metadata
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Try pdfplumber first (better text extraction)
        try:
            text = self._extract_with_pdfplumber(pdf_path)
        except Exception as e:
            print(f"pdfplumber failed, falling back to PyPDF2: {e}")
            text = self._extract_with_pypdf2(pdf_path)
        
        # Extract metadata
        metadata = self._extract_metadata(text, pdf_path)
        
        # Split into sections
        sections = self._split_into_sections(text)
        
        return {
            "full_text": text,
            "sections": sections,
            "metadata": metadata,
            "source_file": str(pdf_path),
            "page_count": metadata.get("page_count", 0)
        }
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber (more accurate)"""
        text_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2 (fallback)"""
        text_parts = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    def _extract_metadata(self, text: str, pdf_path: Path) -> Dict:
        """Extract metadata from text and filename"""
        metadata = {
            "filename": pdf_path.name,
            "doc_type": "report"
        }
        
        # Try to extract project type
        if any(word in text.lower() for word in ["substation", "switchyard", "terminal"]):
            metadata["project_type"] = "substation"
        elif any(word in text.lower() for word in ["solar", "photovoltaic", "pv"]):
            metadata["project_type"] = "solar_farm"
        elif "wind" in text.lower():
            metadata["project_type"] = "wind_farm"
        else:
            metadata["project_type"] = "general"
        
        # Extract voltage level
        voltage_pattern = r"(\d+)\s*kV"
        voltage_matches = re.findall(voltage_pattern, text)
        if voltage_matches:
            voltages = [int(v) for v in voltage_matches]
            # Take the highest voltage mentioned (usually the primary voltage)
            max_voltage = max(voltages)
            if max_voltage <= 1:
                metadata["voltage_level"] = "LV"
            elif max_voltage <= 66:
                metadata["voltage_level"] = "HV"
            else:
                metadata["voltage_level"] = "EHV"
        
        # Extract fault current range
        fault_pattern = r"(\d+(?:\.\d+)?)\s*kA"
        fault_matches = re.findall(fault_pattern, text)
        if fault_matches:
            fault_currents = [float(f) for f in fault_matches]
            max_fault = max(fault_currents)
            if max_fault < 10:
                metadata["fault_current_range"] = "0-10kA"
            elif max_fault < 50:
                metadata["fault_current_range"] = "10-50kA"
            else:
                metadata["fault_current_range"] = "50kA+"
        
        # Extract soil resistivity indication
        if re.search(r"resistivity.*?(\d+)\s*[ΩΩ]", text.lower()):
            soil_values = re.findall(r"(\d+)\s*[ΩΩ]", text)
            if soil_values:
                avg_resistivity = sum(int(v) for v in soil_values) / len(soil_values)
                if avg_resistivity < 100:
                    metadata["soil_resistivity_range"] = "low"
                elif avg_resistivity < 500:
                    metadata["soil_resistivity_range"] = "medium"
                else:
                    metadata["soil_resistivity_range"] = "high"
        
        # Extract standards referenced
        standards = []
        if "AS/NZS 3000" in text or "AS/NZS 3000" in text:
            standards.append("AS/NZS 3000")
        if "AS 2067" in text or "AS2067" in text:
            standards.append("AS 2067")
        if "IEEE 80" in text or "IEEE-80" in text:
            standards.append("IEEE 80")
        if "IEC 61936" in text:
            standards.append("IEC 61936")
        
        if standards:
            metadata["standards_referenced"] = standards
        
        return metadata
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """
        Split document into logical sections based on headers
        
        Returns:
            Dict mapping section_type to text content
        """
        sections = {}
        
        # Split text into lines for processing
        lines = text.split('\n')
        current_section = "introduction"
        current_text = []
        
        for line in lines:
            # Check if line matches a section header
            section_found = False
            for section_name, pattern in self.section_patterns.items():
                if re.search(pattern, line) and len(line) < 100:  # Header lines are typically short
                    # Save previous section
                    if current_text:
                        sections[current_section] = '\n'.join(current_text).strip()
                    
                    # Start new section
                    current_section = section_name
                    current_text = [line]
                    section_found = True
                    break
            
            if not section_found:
                current_text.append(line)
        
        # Save last section
        if current_text:
            sections[current_section] = '\n'.join(current_text).strip()
        
        return sections
    
    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """
        Extract tables from PDF (useful for soil test data, calculation results)
        
        Returns:
            List of tables as dicts
        """
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table:
                            tables.append({
                                "page": page_num + 1,
                                "data": table
                            })
        except Exception as e:
            print(f"Table extraction failed: {e}")
        
        return tables


if __name__ == "__main__":
    # Test the parser
    parser = PDFParser()
    
    # Example usage
    sample_path = Path("../data/historical_reports/sample_report.pdf")
    if sample_path.exists():
        result = parser.parse(str(sample_path))
        print(f"Extracted {len(result['full_text'])} characters")
        print(f"Found {len(result['sections'])} sections")
        print(f"Metadata: {result['metadata']}")