"""
Input Validator - Validate project data before report generation
"""
from typing import Dict, List, Any
import re

class InputValidator:
    """Validate earthing study input data"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, project_data: Dict) -> Dict[str, Any]:
        """
        Validate project input data
        
        Returns:
            Dict with validation status, errors, and warnings
        """
        self.errors = []
        self.warnings = []
        
        # Required field validation
        self._validate_required_fields(project_data)
        
        # Data type and range validation
        self._validate_electrical_data(project_data)
        self._validate_soil_data(project_data)
        self._validate_design_requirements(project_data)
        
        # Engineering logic validation
        self._validate_engineering_logic(project_data)
        
        # Determine overall status
        if self.errors:
            status = "fail"
        elif self.warnings:
            status = "warning"
        else:
            status = "pass"
        
        return {
            "validation_status": status,
            "errors": self.errors,
            "warnings": self.warnings,
            "completeness_score": self._calculate_completeness(project_data)
        }
    
    def _validate_required_fields(self, data: Dict):
        """Check for required fields"""
        required = [
            "project_name",
            "client_name",
            "site_address",
            "voltage_level",
            "fault_current_symmetrical",
            "fault_clearance_time",
            "soil_resistivity_measurements",
            "target_grid_resistance"
        ]
        
        for field in required:
            if field not in data or not data[field]:
                self.errors.append({
                    "field": field,
                    "message": f"Required field '{field}' is missing",
                    "severity": "error"
                })
    
    def _validate_electrical_data(self, data: Dict):
        """Validate electrical system parameters"""
        # Voltage level
        if "voltage_level" in data:
            voltage_str = data["voltage_level"]
            match = re.search(r'(\d+)', voltage_str)
            if match:
                voltage = int(match.group(1))
                if voltage < 0.4 or voltage > 500:
                    self.warnings.append({
                        "field": "voltage_level",
                        "message": f"Voltage {voltage}kV is outside typical range (0.4-500kV)",
                        "severity": "warning"
                    })
            else:
                self.errors.append({
                    "field": "voltage_level",
                    "message": "Cannot extract numeric voltage from voltage_level",
                    "severity": "error"
                })
        
        # Fault current
        if "fault_current_symmetrical" in data:
            fault_current = data["fault_current_symmetrical"]
            if not isinstance(fault_current, (int, float)):
                self.errors.append({
                    "field": "fault_current_symmetrical",
                    "message": "Fault current must be a number",
                    "severity": "error"
                })
            elif fault_current < 0.1 or fault_current > 100:
                self.warnings.append({
                    "field": "fault_current_symmetrical",
                    "message": f"Fault current {fault_current}kA is outside typical range (0.1-100kA)",
                    "severity": "warning"
                })
        
        # Fault clearance time
        if "fault_clearance_time" in data:
            clearance_time = data["fault_clearance_time"]
            if not isinstance(clearance_time, (int, float)):
                self.errors.append({
                    "field": "fault_clearance_time",
                    "message": "Fault clearance time must be a number",
                    "severity": "error"
                })
            elif clearance_time < 0.01 or clearance_time > 5:
                self.warnings.append({
                    "field": "fault_clearance_time",
                    "message": f"Fault clearance time {clearance_time}s is outside typical range (0.01-5s)",
                    "severity": "warning"
                })
    
    def _validate_soil_data(self, data: Dict):
        """Validate soil resistivity data"""
        if "soil_resistivity_measurements" not in data:
            return
        
        measurements = data["soil_resistivity_measurements"]
        
        if not isinstance(measurements, list):
            self.errors.append({
                "field": "soil_resistivity_measurements",
                "message": "Soil measurements must be a list of {depth, resistivity} dicts",
                "severity": "error"
            })
            return
        
        if len(measurements) < 2:
            self.warnings.append({
                "field": "soil_resistivity_measurements",
                "message": "At least 2 measurements recommended for soil modeling",
                "severity": "warning"
            })
        
        for i, measurement in enumerate(measurements):
            if not isinstance(measurement, dict):
                self.errors.append({
                    "field": f"soil_resistivity_measurements[{i}]",
                    "message": "Each measurement must be a dict with 'depth' and 'resistivity'",
                    "severity": "error"
                })
                continue
            
            if "depth" not in measurement or "resistivity" not in measurement:
                self.errors.append({
                    "field": f"soil_resistivity_measurements[{i}]",
                    "message": "Missing 'depth' or 'resistivity' field",
                    "severity": "error"
                })
                continue
            
            depth = measurement["depth"]
            resistivity = measurement["resistivity"]
            
            if depth < 0 or depth > 50:
                self.warnings.append({
                    "field": f"soil_resistivity_measurements[{i}].depth",
                    "message": f"Depth {depth}m is outside typical range (0-50m)",
                    "severity": "warning"
                })
            
            if resistivity < 1 or resistivity > 10000:
                self.warnings.append({
                    "field": f"soil_resistivity_measurements[{i}].resistivity",
                    "message": f"Resistivity {resistivity}Ωm is outside typical range (1-10000Ωm)",
                    "severity": "warning"
                })
    
    def _validate_design_requirements(self, data: Dict):
        """Validate design parameters"""
        if "target_grid_resistance" in data:
            target = data["target_grid_resistance"]
            if not isinstance(target, (int, float)):
                self.errors.append({
                    "field": "target_grid_resistance",
                    "message": "Target grid resistance must be a number",
                    "severity": "error"
                })
            elif target < 0.1 or target > 10:
                self.warnings.append({
                    "field": "target_grid_resistance",
                    "message": f"Target resistance {target}Ω is outside typical range (0.1-10Ω)",
                    "severity": "warning"
                })
    
    def _validate_engineering_logic(self, data: Dict):
        """Validate engineering relationships between parameters"""
        # Check voltage vs fault current consistency
        if "voltage_level" in data and "fault_current_symmetrical" in data:
            voltage_match = re.search(r'(\d+)', data["voltage_level"])
            if voltage_match:
                voltage = int(voltage_match.group(1))
                fault_current = data["fault_current_symmetrical"]
                
                # Typical fault current ranges by voltage
                expected_ranges = {
                    (0, 1): (0.1, 5),      # LV: 0.1-5kA
                    (1, 33): (5, 25),      # MV: 5-25kA
                    (33, 132): (15, 50),   # HV: 15-50kA
                    (132, 500): (30, 80)   # EHV: 30-80kA
                }
                
                for (v_min, v_max), (i_min, i_max) in expected_ranges.items():
                    if v_min < voltage <= v_max:
                        if not (i_min <= fault_current <= i_max):
                            self.warnings.append({
                                "field": "fault_current_symmetrical",
                                "message": f"Fault current {fault_current}kA seems unusual for {voltage}kV system (typical range: {i_min}-{i_max}kA)",
                                "severity": "warning",
                                "suggestion": "Verify with protection studies"
                            })
                        break
    
    def _calculate_completeness(self, data: Dict) -> float:
        """Calculate completeness score (0-1)"""
        total_fields = [
            "project_name", "client_name", "site_address", "project_number",
            "engineer_name", "voltage_level", "fault_current_symmetrical",
            "fault_clearance_time", "soil_resistivity_measurements",
            "target_grid_resistance", "project_type", "transformer_rating",
            "site_length", "site_width", "earth_conductor_size"
        ]
        
        present_fields = sum(1 for field in total_fields if field in data and data[field])
        
        return present_fields / len(total_fields)


if __name__ == "__main__":
    # Test validator
    validator = InputValidator()
    
    test_data = {
        "project_name": "Test Substation",
        "client_name": "Test Client",
        "site_address": "123 Test St",
        "voltage_level": "33kV",
        "fault_current_symmetrical": 25.0,
        "fault_clearance_time": 0.5,
        "soil_resistivity_measurements": [
            {"depth": 1.0, "resistivity": 150.0},
            {"depth": 3.0, "resistivity": 200.0}
        ],
        "target_grid_resistance": 1.0
    }
    
    result = validator.validate(test_data)
    print(f"Status: {result['validation_status']}")
    print(f"Completeness: {result['completeness_score']:.2%}")
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")