"""
Input Validator - Validate comprehensive report generation input data
"""
from typing import Dict, List, Any, Tuple, Union
import json


class InputValidator:
    """Validates comprehensive input data for report generation"""
    
    # Define required section structure
    REQUIRED_SECTIONS = {
        'project_info': dict,
        'site_data': dict,
        'electrical_system': dict,
        'earthing_design': dict,
    }
    
    # Required fields within each section
    SECTION_REQUIREMENTS = {
        'project_info': ['project_name', 'project_number', 'location', 'client', 'date'],
        'site_data': ['soil_resistivity', 'site_conditions'],
        'electrical_system': ['voltage_level', 'system_type', 'fault_current'],
        'earthing_design': ['grid_configuration', 'supplementary_electrodes'],
    }
    
    def __init__(self):
        """Initialize validator"""
        pass
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate comprehensive input data
        
        Args:
            data: Input dictionary with full structure
            
        Returns:
            Validation result with detailed status
        """
        errors = []
        warnings = []
        missing_sections = []
        
        # ============================================================
        # CHECK TOP-LEVEL STRUCTURE
        # ============================================================
        for section, section_type in self.REQUIRED_SECTIONS.items():
            if section not in data:
                missing_sections.append(section)
                errors.append({
                    'field': section,
                    'message': f"Required section '{section}' is missing",
                    'severity': 'error',
                    'location': 'root'
                })
            elif not isinstance(data[section], section_type):
                errors.append({
                    'field': section,
                    'message': f"Section '{section}' must be a {section_type.__name__}",
                    'severity': 'error',
                    'location': 'root'
                })
        
        # ============================================================
        # VALIDATE EACH SECTION
        # ============================================================
        if 'project_info' in data:
            errors.extend(self._validate_project_info(data['project_info']))
        
        if 'site_data' in data:
            errors.extend(self._validate_site_data(data['site_data']))
        
        if 'electrical_system' in data:
            errors.extend(self._validate_electrical_system(data['electrical_system']))
        
        if 'earthing_design' in data:
            errors.extend(self._validate_earthing_design(data['earthing_design']))
        
        if 'standards_compliance' in data:
            errors.extend(self._validate_standards(data['standards_compliance']))
        
        if 'calculation_requirements' in data:
            warnings.extend(self._validate_calculations(data['calculation_requirements']))
        
        # ============================================================
        # CALCULATE COMPLETENESS
        # ============================================================
        completeness = self._calculate_completeness(data)
        
        # ============================================================
        # DETERMINE STATUS
        # ============================================================
        status = 'pass' if not errors else 'fail'
        
        return {
            'validation_status': status,
            'completeness_score': completeness,
            'sections_provided': len([s for s in self.REQUIRED_SECTIONS if s in data]),
            'sections_total': len(self.REQUIRED_SECTIONS),
            'errors': errors,
            'warnings': warnings,
            'missing_sections': missing_sections,
            'valid_data': data if status == 'pass' else None
        }
    
    def _validate_project_info(self, data: Dict) -> List[Dict]:
        """Validate project info section"""
        errors = []
        required = ['project_name', 'project_number', 'location', 'client', 'date']
        
        for field in required:
            if field not in data or not data[field]:
                errors.append({
                    'field': field,
                    'message': f"Required field '{field}' is missing or empty",
                    'severity': 'error',
                    'location': 'project_info'
                })
        
        return errors
    
    def _validate_site_data(self, data: Dict) -> List[Dict]:
        """Validate site data section"""
        errors = []
        
        # Check soil resistivity
        if 'soil_resistivity' in data:
            sr = data['soil_resistivity']
            if isinstance(sr, dict):
                if 'measurements' not in sr or not sr['measurements']:
                    errors.append({
                        'field': 'soil_resistivity.measurements',
                        'message': "Soil resistivity measurements are required",
                        'severity': 'error',
                        'location': 'site_data'
                    })
                if 'soil_type' not in sr or not sr['soil_type']:
                    errors.append({
                        'field': 'soil_resistivity.soil_type',
                        'message': "Soil type must be specified",
                        'severity': 'warning',
                        'location': 'site_data'
                    })
        
        # Check site conditions
        if 'site_conditions' in data:
            sc = data['site_conditions']
            if isinstance(sc, dict):
                if 'terrain' not in sc or not sc['terrain']:
                    errors.append({
                        'field': 'site_conditions.terrain',
                        'message': "Terrain type must be specified",
                        'severity': 'warning',
                        'location': 'site_data'
                    })
                if 'water_table_depth' in sc:
                    if not isinstance(sc['water_table_depth'], (int, float)) or sc['water_table_depth'] < 0:
                        errors.append({
                            'field': 'site_conditions.water_table_depth',
                            'message': "Water table depth must be a positive number",
                            'severity': 'error',
                            'location': 'site_data'
                        })
        
        return errors
    
    def _validate_electrical_system(self, data: Dict) -> List[Dict]:
        """Validate electrical system section"""
        errors = []
        
        # Validate voltage level
        valid_voltages = ['11kV', '22kV', '33kV', '66kV', '110kV', '132kV', '220kV', '275kV', '330kV']
        if 'voltage_level' in data and data['voltage_level'] not in valid_voltages:
            errors.append({
                'field': 'electrical_system.voltage_level',
                'message': f"Voltage level '{data['voltage_level']}' may be invalid",
                'severity': 'warning',
                'location': 'electrical_system'
            })
        
        # Validate fault currents
        if 'fault_current' in data:
            fc = data['fault_current']
            if isinstance(fc, dict):
                for field in ['three_phase', 'single_phase_to_ground', 'duration']:
                    if field in fc:
                        if not isinstance(fc[field], (int, float)) or fc[field] <= 0:
                            errors.append({
                                'field': f'electrical_system.fault_current.{field}',
                                'message': f"{field} must be a positive number",
                                'severity': 'error',
                                'location': 'electrical_system'
                            })
        
        # Validate equipment list
        if 'equipment' in data and not isinstance(data['equipment'], list):
            errors.append({
                'field': 'electrical_system.equipment',
                'message': "Equipment must be a list",
                'severity': 'error',
                'location': 'electrical_system'
            })
        
        return errors
    
    def _validate_earthing_design(self, data: Dict) -> List[Dict]:
        """Validate earthing design section"""
        errors = []
        
        if 'grid_configuration' not in data:
            errors.append({
                'field': 'earthing_design.grid_configuration',
                'message': "Grid configuration is required",
                'severity': 'error',
                'location': 'earthing_design'
            })
        else:
            gc = data['grid_configuration']
            # Validate grid parameters
            for field in ['area', 'conductor_size', 'burial_depth', 'total_length']:
                if field in gc:
                    if not isinstance(gc[field], (int, float)) or gc[field] <= 0:
                        errors.append({
                            'field': f'earthing_design.grid_configuration.{field}',
                            'message': f"{field} must be a positive number",
                            'severity': 'error',
                            'location': 'earthing_design'
                        })
        
        if 'supplementary_electrodes' not in data:
            errors.append({
                'field': 'earthing_design.supplementary_electrodes',
                'message': "Supplementary electrodes definition is required",
                'severity': 'warning',
                'location': 'earthing_design'
            })
        
        return errors
    
    def _validate_standards(self, data: Union[List, Dict]) -> List[Dict]:
        """Validate standards compliance section"""
        errors = []
        
        if isinstance(data, dict):
            if 'primary_standards' not in data or not data['primary_standards']:
                errors.append({
                    'field': 'standards_compliance.primary_standards',
                    'message': "At least one primary standard should be specified",
                    'severity': 'warning',
                    'location': 'standards_compliance'
                })
        elif isinstance(data, list):
            if len(data) == 0:
                errors.append({
                    'field': 'standards_compliance',
                    'message': "At least one standard should be specified",
                    'severity': 'warning',
                    'location': 'standards_compliance'
                })
        
        return errors
    
    def _validate_calculations(self, data: Dict) -> List[Dict]:
        """Validate calculation requirements"""
        warnings = []
        
        if isinstance(data, dict):
            # Check if at least some calculations are required
            calc_fields = ['grid_resistance', 'gpr_analysis', 'touch_potential', 'step_potential', 'conductor_sizing']
            enabled_calcs = sum(1 for f in calc_fields if data.get(f, {}).get('calculate', False))
            
            if enabled_calcs == 0:
                warnings.append({
                    'field': 'calculation_requirements',
                    'message': "No calculations are enabled",
                    'severity': 'warning',
                    'location': 'calculation_requirements'
                })
        
        return warnings
    
    def _calculate_completeness(self, data: Dict) -> float:
        """Calculate data completeness percentage"""
        total_checks = 0
        passed_checks = 0
        
        # Section checks
        for section in self.REQUIRED_SECTIONS:
            total_checks += 1
            if section in data and data[section]:
                passed_checks += 1
        
        # Optional sections
        optional_sections = ['standards_compliance', 'calculation_requirements', 'safety_requirements', 'maintenance_plan']
        for section in optional_sections:
            total_checks += 0.5  # Weight less than required sections
            if section in data and data[section]:
                passed_checks += 0.5
        
        return min(1.0, passed_checks / total_checks) if total_checks > 0 else 0.0
    
    def get_template(self) -> Dict[str, Any]:
        """Return comprehensive template"""
        # Load from the actual file
        try:
            import json
            from pathlib import Path
            template_path = Path(__file__).parent.parent.parent / 'test_data' / 'inputs' / 'input_data.json'
            if template_path.exists():
                with open(template_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        # Fallback
        return {
            "project_info": {
                "project_name": "Example Substation",
                "project_number": "ES-2024-001",
                "location": "Location, State, Country",
                "client": "Client Name",
                "date": "2024-12-05",
                "prepared_by": "Engineer Name",
                "reviewed_by": "Manager Name"
            },
            "site_data": {
                "soil_resistivity": {
                    "measurements": [
                        {"depth": "0-2m", "resistivity": 150, "method": "Wenner four-probe"},
                        {"depth": "2-5m", "resistivity": 280, "method": "Wenner four-probe"}
                    ],
                    "average_resistivity": 215.0,
                    "soil_type": "Clay",
                    "test_date": "2024-10-15"
                },
                "site_conditions": {
                    "terrain": "Flat",
                    "water_table_depth": 5.0
                }
            },
            "electrical_system": {
                "voltage_level": "33kV",
                "system_type": "distribution_substation",
                "fault_current": {
                    "three_phase": 10.0,
                    "single_phase_to_ground": 8.0,
                    "duration": 1.0
                }
            },
            "earthing_design": {
                "grid_configuration": {
                    "area": 1000.0,
                    "conductor_size": 95,
                    "burial_depth": 0.6,
                    "total_length": 500.0
                },
                "supplementary_electrodes": {
                    "type": "Vertical rods",
                    "quantity": 10,
                    "length": 3.0
                }
            }
        }
    
    def print_schema(self):
        """Print schema overview"""
        print("\n" + "="*70)
        print("INPUT SCHEMA - Comprehensive Earthing Design Validator")
        print("="*70)
        
        print("\n✅ REQUIRED SECTIONS:")
        for section in self.REQUIRED_SECTIONS:
            reqs = self.SECTION_REQUIREMENTS.get(section, [])
            print(f"\n  {section}:")
            print(f"    Required fields: {', '.join(reqs)}")
        
        print("\n⚠️  OPTIONAL SECTIONS:")
        optional = ['standards_compliance', 'calculation_requirements', 'safety_requirements', 
                   'maintenance_plan', 'environmental_impact']
        for section in optional:
            print(f"    - {section}")
        
        print("\n📋 Full example: backend/test_data/inputs/input_data.json")
        print("="*70 + "\n")