import React, { useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Grid } from '@react-three/drei'

export default function App() {
  const [lpsClass, setLpsClass] = useState('I')
  const [buildingHeight, setBuildingHeight] = useState(15)
  const [distance, setDistance] = useState(0.8)
  const [results, setResults] = useState<any>(null)

  // 3D Viewport Controls & Layers
  const [showBuilding, setShowBuilding] = useState(true)
  const [showConductors, setShowConductors] = useState(true)
  const [showProtectionEnvelope, setShowProtectionEnvelope] = useState(true)
  const [cameraView, setCameraView] = useState<'iso' | 'top' | 'front' | 'side'>('iso')

  const runCalculation = async () => {
    const payload = {
      name: "3D Sample Building",
      lps_class: lpsClass,
      building: { length_m: 20, width_m: 10, height_m: buildingHeight, roof_type: "flat" },
      nodes: [
        { id: "node-1", x: 0, y: 0, z: buildingHeight, node_type: "air_termination" }
      ],
      segments: [],
      separation_points: [
        {
          id: "sp-1",
          name: "HVAC Unit A",
          x: 2, y: 2, z: buildingHeight,
          associated_node_id: "node-1",
          insulation_medium: "air",
          physical_distance_m: distance
        }
      ]
    }

    try {
      const res = await fetch('http://localhost:8000/api/v1/calculations/separation-distance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await res.json()
      setResults(data)
    } catch (e) {
      console.error(e)
    }
  }

  const getCameraPos = (): [number, number, number] => {
    switch (cameraView) {
      case 'top': return [0, 50, 0]
      case 'front': return [0, buildingHeight / 2, 40]
      case 'side': return [40, buildingHeight / 2, 0]
      default: return [25, 25, 25]
    }
  }

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh' }}>
      {/* Sidebar Controls */}
      <div style={{ width: '380px', padding: '20px', backgroundColor: '#1e293b', borderRight: '1px solid #334155', overflowY: 'auto' }}>
        <h2 style={{ color: '#38bdf8', marginTop: 0 }}>AegisLPS Workbench</h2>
        <p style={{ fontSize: '12px', color: '#94a3b8' }}>Prototype Version 1.0.0-alpha.1 | IEC 62305-3:2024</p>

        {/* Viewport Presets & Layers */}
        <div style={{ marginBottom: '15px', padding: '10px', background: '#0f172a', borderRadius: '4px' }}>
          <span style={{ fontSize: '13px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>Camera Preset:</span>
          <div style={{ display: 'flex', gap: '6px' }}>
            {(['iso', 'top', 'front', 'side'] as const).map(mode => (
              <button
                key={mode}
                onClick={() => setCameraView(mode)}
                style={{
                  flex: 1,
                  padding: '5px',
                  background: cameraView === mode ? '#0284c7' : '#334155',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  textTransform: 'uppercase',
                  fontSize: '11px'
                }}
              >
                {mode}
              </button>
            ))}
          </div>

          <span style={{ fontSize: '13px', fontWeight: 'bold', display: 'block', margin: '10px 0 6px 0' }}>Display Layers:</span>
          <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px' }}>
            <input type="checkbox" checked={showBuilding} onChange={e => setShowBuilding(e.target.checked)} /> Building Geometry
          </label>
          <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px' }}>
            <input type="checkbox" checked={showConductors} onChange={e => setShowConductors(e.target.checked)} /> Conductors & Rods
          </label>
          <label style={{ display: 'block', fontSize: '12px' }}>
            <input type="checkbox" checked={showProtectionEnvelope} onChange={e => setShowProtectionEnvelope(e.target.checked)} /> Protection Envelope (20m Sphere)
          </label>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontSize: '14px', marginBottom: '5px' }}>LPS Class:</label>
          <select value={lpsClass} onChange={e => setLpsClass(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#0f172a', color: '#fff', border: '1px solid #475569' }}>
            <option value="I">Class I (ki = 0.08)</option>
            <option value="II">Class II (ki = 0.06)</option>
            <option value="III">Class III/IV (ki = 0.04)</option>
          </select>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontSize: '14px', marginBottom: '5px' }}>Building Height (m):</label>
          <input type="number" value={buildingHeight} onChange={e => setBuildingHeight(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#0f172a', color: '#fff', border: '1px solid #475569' }} />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontSize: '14px', marginBottom: '5px' }}>Actual Physical Clearance (m):</label>
          <input type="number" step="0.1" value={distance} onChange={e => setDistance(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#0f172a', color: '#fff', border: '1px solid #475569' }} />
        </div>

        <button onClick={runCalculation} style={{ width: '100%', padding: '10px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
          Calculate Separation Distance
        </button>

        {results && (
          <div style={{ marginTop: '20px', padding: '15px', backgroundColor: results[0].pass_compliance ? '#064e3b' : '#7f1d1d', borderRadius: '6px' }}>
            <h4 style={{ margin: '0 0 10px 0' }}>Result: {results[0].pass_compliance ? 'COMPLIANT (PASS)' : 'NON-COMPLIANT (FAIL)'}</h4>
            <p style={{ fontSize: '13px', margin: '4px 0' }}><b>Required (s):</b> {results[0].required_distance_s_m.toFixed(3)} m</p>
            <p style={{ fontSize: '13px', margin: '4px 0' }}><b>Actual Clearance:</b> {results[0].actual_distance_m.toFixed(3)} m</p>
            <p style={{ fontSize: '13px', margin: '4px 0' }}><b>Safety Margin:</b> {results[0].safety_margin_m.toFixed(3)} m</p>
            <p style={{ fontSize: '11px', color: '#cbd5e1', marginTop: '10px', fontFamily: 'monospace' }}>{results[0].formula_trace}</p>
          </div>
        )}
      </div>

      {/* 3D WebGL Viewport */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas camera={{ position: getCameraPos(), fov: 50 }}>
          <ambientLight intensity={0.7} />
          <directionalLight position={[20, 30, 10]} intensity={1.2} />
          <Grid args={[50, 50]} cellColor="#334155" sectionColor="#0284c7" />
          <OrbitControls />

          {/* 3D Parametric Building Box */}
          {showBuilding && (
            <mesh position={[0, buildingHeight / 2, 0]}>
              <boxGeometry args={[20, buildingHeight, 10]} />
              <meshStandardMaterial color="#334155" wireframe={false} opacity={0.8} transparent />
            </mesh>
          )}

          {/* Air Termination Mast & Down Conductor */}
          {showConductors && (
            <group>
              <mesh position={[0, buildingHeight + 1.5, 0]}>
                <cylinderGeometry args={[0.05, 0.05, 3]} />
                <meshStandardMaterial color="#f59e0b" />
              </mesh>
              {/* Down conductor trace along building corner */}
              <mesh position={[10, buildingHeight / 2, 5]}>
                <cylinderGeometry args={[0.03, 0.03, buildingHeight]} />
                <meshStandardMaterial color="#38bdf8" />
              </mesh>
            </group>
          )}

          {/* Rolling Sphere Protection Envelope (Semi-transparent sphere) */}
          {showProtectionEnvelope && (
            <mesh position={[0, buildingHeight + 3, 0]}>
              <sphereGeometry args={[20, 32, 16]} />
              <meshStandardMaterial color="#38bdf8" wireframe={true} opacity={0.2} transparent />
            </mesh>
          )}
        </Canvas>
      </div>
    </div>
  )
}
