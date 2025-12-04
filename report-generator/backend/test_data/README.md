# Test Data for Earthing Report Generator

This directory contains sample data for testing and developing the AI report generator.

## Directory Structure

```
test_data/
├── sample_reports/          # Example earthing study reports (text format)
│   ├── sample_33kV_substation_report.txt
│   └── sample_solar_farm_report.txt
├── inputs/                  # Test input data (JSON format)
│   ├── input_commercial_lv.json
│   ├── input_11kV_substation.json
│   ├── input_33kV_substation_sunnybank.json
│   └── input_132kV_solar_farm.json
└── standards/              # Standards reference documents
    └── australian_earthing_standards_reference.txt
```

## Sample Reports

### 1. sample_33kV_substation_report.txt
**Complete earthing study for a 33kV distribution substation**

- **Project:** Sunnybank Distribution Substation
- **Voltage:** 33kV
- **Capacity:** 20 MVA
- **Fault Current:** 25 kA
- **Soil:** Two-layer (150/220 Ωm)
- **Key Features:**
  - Full calculations (grid resistance, touch/step potentials)
  - Schwarz method for earth resistance
  - IEEE 80 safety analysis
  - AS/NZS 3000, AS 2067 compliance
  - Conductor sizing per AS/NZS 3008

### 2. sample_solar_farm_report.txt
**Earthing study for 50MW solar farm with 132kV connection**

- **Project:** Darling Downs Solar Farm
- **Voltages:** 132kV, 33kV, 1000V DC
- **Capacity:** 50 MW
- **Fault Current:** 31.5 kA
- **Soil:** High resistivity (450-850 Ωm)
- **Key Features:**
  - Multi-voltage system integration
  - High resistivity soil design challenges
  - Lightning protection considerations
  - AS/NZS 5033 (PV arrays) compliance
  - Distributed inverter station earthing

## Test Inputs

### input_commercial_lv.json
**Low voltage commercial installation**
- 415V shopping centre main switchboard
- 45 kA fault current
- Good soil conditions (85-110 Ωm)
- Urban environment with services

### input_11kV_substation.json
**Medium voltage distribution substation**
- 11kV substation at Brisbane Airport
- 18.5 kA fault current
- Moderate soil resistivity (320-465 Ωm)
- Flood zone considerations
- Corrosion protection required

### input_33kV_substation_sunnybank.json
**Matches the sample report for validation**
- 33kV residential area substation
- 25 kA fault current
- Two-layer soil (145-215 Ωm)
- Use this to test against the sample report

### input_132kV_solar_farm.json
**Matches the solar farm sample report**
- 132kV solar farm switching station
- 31.5 kA fault current
- High resistivity soil (442-838 Ωm)
- Multi-voltage considerations

## Standards Reference

**australian_earthing_standards_reference.txt**

Comprehensive reference document containing:

1. **AS/NZS 3000:2018** - Electrical Installations (Wiring Rules)
   - Earthing conductor requirements
   - Minimum sizes
   - Connection methods
   - Bonding requirements

2. **AS 2067:2016** - Substations and High Voltage Installations
   - Earth resistance limits
   - Touch/step potential requirements
   - Grid construction standards
   - Conductor sizing

3. **IEEE 80-2013** - AC Substation Grounding
   - Safety voltage calculations
   - Grid resistance formulas
   - Design procedures
   - Mesh and step voltage equations

4. **AS/NZS 3008.1.1** - Conductor Sizing
   - Adiabatic equation for fault current
   - Material constants
   - Temperature limits

5. **AS/NZS 5033** - Photovoltaic Arrays
   - PV array earthing requirements
   - DC system earthing
   - Lightning protection

Plus:
- Compliance statement templates
- Typical design values for Australia
- Soil resistivity ranges
- Fault current ranges by voltage class

## How to Use This Test Data

### 1. Manual Review
Read the sample reports to understand:
- Report structure and sections
- Technical language and terminology
- Calculation methods and presentation
- Compliance statement formats

### 2. RAG System Training
The sample reports can be used to:
- Test document parsing (PDF/DOCX → text extraction)
- Validate chunking strategies
- Test embedding generation
- Verify retrieval quality

**Note:** Sample reports are provided as .txt files (extracted text). In production, you'll ingest actual PDF/DOCX files.

### 3. Input Validation Testing
Test the input validator with the sample JSON files:

```bash
cd backend
python -c "
from app.generation.validator import InputValidator
import json

with open('../test_data/inputs/input_33kV_substation_sunnybank.json') as f:
    data = json.load(f)

validator = InputValidator()
result = validator.validate(data)
print(f'Status: {result[\"validation_status\"]}')
print(f'Completeness: {result[\"completeness_score\"]:.1%}')
"
```

### 4. Report Generation Testing
Use the test inputs to generate reports:

```bash
# Once generation is implemented
curl -X POST http://localhost:8000/api/v1/generate-report \
  -H "Content-Type: application/json" \
  -d @test_data/inputs/input_33kV_substation_sunnybank.json
```

### 5. Compare Generated vs Sample
Use the matching pairs to validate output quality:
- Generate report from `input_33kV_substation_sunnybank.json`
- Compare to `sample_33kV_substation_report.txt`
- Check technical accuracy, language, and completeness

## Running All Tests

Use the provided test script:

```bash
python test_samples.py
```

This will:
1. Validate all input files
2. Test the embedding system
3. Check standards reference
4. Test RAG retrieval (if data ingested)
5. Show summary of available test data

## Adding Your Own Test Data

### To add more sample reports:
1. Place PDF/DOCX files in: `backend/data/historical_reports/`
2. Run ingestion: `python -m app.ingestion.ingest_all`
3. These become part of the RAG knowledge base

### To add more test inputs:
1. Create JSON file in `test_data/inputs/`
2. Follow the schema from existing examples
3. Include all required fields:
   - project_name, client_name, site_address
   - voltage_level, fault_current_symmetrical, fault_clearance_time
   - soil_resistivity_measurements (list of {depth, resistivity})
   - target_grid_resistance, project_type

### To add more standards:
1. Create .txt file in `test_data/standards/`
2. Include clause numbers, equations, and compliance requirements
3. Format for easy parsing and retrieval

## Test Data Quality

These samples were created to be:
- ✅ **Technically accurate** - Based on real Australian standards
- ✅ **Representative** - Cover common project types (LV, HV, EHV)
- ✅ **Comprehensive** - Include all major report sections
- ✅ **Realistic** - Use typical Australian soil, fault levels, voltages
- ✅ **Validated** - Calculations verified against standards

## Notes for Development

1. **Sample reports are text files** - They simulate extracted PDF content. Real production will use actual PDF/DOCX files.

2. **Standards reference is condensed** - Real standards documents are hundreds of pages. This is a curated extract of the most relevant clauses for AI reference.

3. **Soil resistivity values** - Based on typical Australian conditions. Queensland tends to have sandy soils (100-500 Ωm). Inland areas can be higher (500-1000 Ωm).

4. **Fault currents** - Based on typical Energex/Ergon Energy networks in Queensland. Your area may vary.

5. **Matching pairs** - The Sunnybank and Darling Downs inputs match their respective sample reports. Use these for validation.

## What's Missing (Intentionally)

This test data does NOT include:
- ❌ Actual client/project details (all anonymized/fictional)
- ❌ Proprietary calculation software outputs
- ❌ Full standards documents (copyright - use official sources)
- ❌ Site-specific drawings or photos
- ❌ Actual contractor quotes or cost estimates

These would be provided by real clients in production use.

## License Note

Sample reports are fictional examples created for testing purposes. 
Standards references are excerpts for educational/development use.
Always refer to official published standards for compliance work.

## Questions?

See the main README.md and MVP_STATUS.md for more information about:
- How the system works
- What to build next
- How to use this test data in development