import React, { useState } from 'react';
import { SafeAreaView, ScrollView, View, Text, TextInput, Button, StyleSheet, Alert } from 'react-native';

// Shape matches backend input_data.json (simplified)
type InputData = {
  project_info: {
    project_name: string;
    project_number: string;
    client: string;
    location: string;
    date: string;
    prepared_by?: string;
    reviewed_by?: string;
  };
  site_data: {
    soil_resistivity: {
      average_resistivity: number;
      soil_type?: string;
    };
  };
  electrical_system: {
    voltage_level: string;
    system_type?: string;
    fault_current: {
      three_phase: number;               // kA
      single_phase_to_ground?: number;   // kA
      duration: number;                  // s
    };
  };
  earthing_design: {
    grid_configuration: {
      area: number;          // m²
      length: number;        // m
      width: number;         // m
      mesh_spacing: number;  // m
      conductor_size: number;// mm²
      burial_depth: number;  // m
      total_length: number;  // m
    };
    surface_treatment?: {
      resistivity?: number;  // Ω·m
    };
  };
};

const API_BASE = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function App() {
  const [data, setData] = useState<InputData>({
    project_info: {
      project_name: '',
      project_number: '',
      client: '',
      location: '',
      date: '',
      prepared_by: '',
      reviewed_by: '',
    },
    site_data: {
      soil_resistivity: {
        average_resistivity: 100,
        soil_type: '',
      },
    },
    electrical_system: {
      voltage_level: '',
      system_type: '',
      fault_current: {
        three_phase: 10,
        single_phase_to_ground: 8,
        duration: 1,
      },
    },
    earthing_design: {
      grid_configuration: {
        area: 1000,
        length: 50,
        width: 20,
        mesh_spacing: 5,
        conductor_size: 70,
        burial_depth: 0.6,
        total_length: 500,
      },
      surface_treatment: {
        resistivity: 3000,
      },
    },
  });

  const onChange = (path: string, value: string) => {
    // Simple path setter (string/number)
    setData(prev => {
      const clone: any = { ...prev };
      const keys = path.split('.');
      let ref = clone;
      for (let i = 0; i < keys.length - 1; i++) ref = ref[keys[i]];
      const last = keys[keys.length - 1];
      const num = Number(value);
      ref[last] = isNaN(num) ? value : num;
      return clone;
    });
  };

  const submit = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/generate-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      Alert.alert('Success', 'Report generation started.');
      console.log(json);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.h1}>Earthing Report Input</Text>

        <Text style={styles.h2}>Project Info</Text>
        {renderText('Project Name', 'project_info.project_name')}
        {renderText('Project Number', 'project_info.project_number')}
        {renderText('Client', 'project_info.client')}
        {renderText('Location', 'project_info.location')}
        {renderText('Date', 'project_info.date')}

        <Text style={styles.h2}>Soil Resistivity</Text>
        {renderText('Average Resistivity (Ω·m)', 'site_data.soil_resistivity.average_resistivity', true)}

        <Text style={styles.h2}>Electrical System</Text>
        {renderText('Voltage Level', 'electrical_system.voltage_level')}
        {renderText('3φ Fault (kA)', 'electrical_system.fault_current.three_phase', true)}
        {renderText('1φ-G Fault (kA)', 'electrical_system.fault_current.single_phase_to_ground', true)}
        {renderText('Fault Duration (s)', 'electrical_system.fault_current.duration', true)}

        <Text style={styles.h2}>Earthing Grid</Text>
        {renderText('Area (m²)', 'earthing_design.grid_configuration.area', true)}
        {renderText('Length (m)', 'earthing_design.grid_configuration.length', true)}
        {renderText('Width (m)', 'earthing_design.grid_configuration.width', true)}
        {renderText('Mesh Spacing (m)', 'earthing_design.grid_configuration.mesh_spacing', true)}
        {renderText('Conductor Size (mm²)', 'earthing_design.grid_configuration.conductor_size', true)}
        {renderText('Burial Depth (m)', 'earthing_design.grid_configuration.burial_depth', true)}
        {renderText('Total Length (m)', 'earthing_design.grid_configuration.total_length', true)}
        {renderText('Surface Resistivity (Ω·m)', 'earthing_design.surface_treatment.resistivity', true)}

        <View style={styles.btnWrap}>
          <Button title="Submit to FastAPI" onPress={submit} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );

  function renderText(label: string, path: string, numeric = false) {
    const value = path.split('.').reduce((o: any, k) => (o ? o[k] : ''), data) ?? '';
    return (
      <View style={styles.field} key={path}>
        <Text style={styles.label}>{label}</Text>
        <TextInput
          style={styles.input}
          value={String(value)}
          keyboardType={numeric ? 'numeric' : 'default'}
          onChangeText={v => onChange(path, v)}
        />
      </View>
    );
  }
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#f8fafc' },
  container: { padding: 16, paddingBottom: 48 },
  h1: { fontSize: 24, fontWeight: '700', marginBottom: 12 },
  h2: { fontSize: 16, fontWeight: '600', marginTop: 18, marginBottom: 6 },
  field: { marginBottom: 10 },
  label: { fontSize: 14, marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 6,
    padding: 10,
    backgroundColor: '#fff',
  },
  btnWrap: { marginTop: 20, marginBottom: 30 },
});