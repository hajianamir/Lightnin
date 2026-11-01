import React, { useState, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Grid, Line, Html } from '@react-three/drei'

interface Node3D {
  id: string
  x: number
  y: number
  z: number
  type: string
}

interface Segment3D {
  id: string
  start: string
  end: string
  kc?: number
}

export default function App() {
  const [lpsClass, setLpsClass] = useState<'I' | 'II' | 'III'>('I')
  const [buildingLength, setBuildingLength] = useState(30)
  const [buildingWidth, setBuildingWidth] = useState(20)
  const [buildingHeight, setBuildingHeight] = useState(15)
  const [physicalClearance, setPhysicalClearance] = useState(1.1)

  // 3D Visualization Controls & Layer States
  const [cameraView, setCameraView] = useState<'iso' | 'top' | 'front' | 'side'>('iso')
  const [showBuilding, setShowBuilding] = useState(true)
  const [showMeshGrid, setShowMeshGrid] = useState(true)
  const [showRods, setShowRods] = useState(true)
  const [showDownConductors, setShowDownConductors] = useState(true)
  const [showSpherePenetration, setShowSpherePenetration] = useState(true)
  const [showCurrentHeatmap, setShowCurrentHeatmap] = useState(true)
  const [showEquipment, setShowEquipment] = useState(true)

  // Calculation Results
  const [calcResult, setCalcResult] = useState<any>(null)
  const [nodalResult, setNodalResult] = useState<any>(null)

  // Rolling sphere radius per IEC 62305-3:2024 Table 2
  const sphereRadius = useMemo(() => {
    switch (lpsClass) {
      case 'I': return 20.0
      case 'II': return 30.0
      case 'III': return 45.0
      default: return 20.0
    }
  }, [lpsClass])

  // Rod configuration (4 perimeter rods + 1 central mast)
  const rodHeight = 3.0
  const rods = useMemo(() => [
    { id: 'rod-1', x: -buildingLength / 3, y: buildingHeight, z: -buildingWidth / 3 },
    { id: 'rod-2', x: buildingLength / 3, y: buildingHeight, z: -buildingWidth / 3 },
    { id: 'rod-3', x: buildingLength / 3, y: buildingHeight, z: buildingWidth / 3 },
    { id: 'rod-4', x: -buildingLength / 3, y: buildingHeight, z: buildingWidth / 3 },
    { id: 'rod-center', x: 0, y: buildingHeight, z: 0 },
  ], [buildingLength, buildingWidth, buildingHeight])

  // Down-conductor corners
  const downConductors = useMemo(() => [
    { id: 'dc-1', x: -buildingLength / 2, z: -buildingWidth / 2 },
    { id: 'dc-2', x: buildingLength / 2, z: -buildingWidth / 2 },
    { id: 'dc-3', x: buildingLength / 2, z: buildingWidth / 2 },
    { id: 'dc-4', x: -buildingLength / 2, z: buildingWidth / 2 },
  ], [buildingLength, buildingWidth])

  // Target object on roof (e.g. rooftop HVAC unit)
  const targetEquipment = {
    x: 4.0,
    y: buildingHeight + 1.2,
    z: 3.0,
    size: [2.5, 2.0, 2.0] as [number, number, number]
  }

  // Camera coordinates based on preset
  const getCameraPos = (): [number, number, number] => {
    switch (cameraView) {
      case 'top': return [0, buildingHeight + 50, 0.001]
      case 'front': return [0, buildingHeight / 2, buildingWidth + 40]
      case 'side': return [buildingLength + 40, buildingHeight / 2, 0]
      default: return [35, buildingHeight + 25, 35]
    }
  }

  const runEngineeringCalculations = async () => {
    const payload = {
      name: `Facility L${lpsClass} - Advanced Engineering Assessment`,
      lps_class: lpsClass,
      building: {
        length_m: buildingLength,
        width_m: buildingWidth,
        height_m: buildingHeight,
        roof_type: "flat"
      },
      nodes: [
        { id: "node-c1", x: downConductors[0].x, y: downConductors[0].z, z: buildingHeight, node_type: "air_termination" },
        { id: "node-c2", x: downConductors[1].x, y: downConductors[1].z, z: buildingHeight, node_type: "air_termination" },
        { id: "node-c3", x: downConductors[2].x, y: downConductors[2].z, z: buildingHeight, node_type: "air_termination" },
        { id: "node-c4", x: downConductors[3].x, y: downConductors[3].z, z: buildingHeight, node_type: "air_termination" },
        { id: "earth-1", x: downConductors[0].x, y: downConductors[0].z, z: 0, node_type: "earth_point" },
        { id: "earth-2", x: downConductors[1].x, y: downConductors[1].z, z: 0, node_type: "earth_point" },
        { id: "earth-3", x: downConductors[2].x, y: downConductors[2].z, z: 0, node_type: "earth_point" },
        { id: "earth-4", x: downConductors[3].x, y: downConductors[3].z, z: 0, node_type: "earth_point" }
      ],
      segments: [
        { id: "seg-dc1", start_node_id: "node-c1", end_node_id: "earth-1", cross_section_mm2: 50 },
        { id: "seg-dc2", start_node_id: "node-c2", end_node_id: "earth-2", cross_section_mm2: 50 },
        { id: "seg-dc3", start_node_id: "node-c3", end_node_id: "earth-3", cross_section_mm2: 50 },
        { id: "seg-dc4", start_node_id: "node-c4", end_node_id: "earth-4", cross_section_mm2: 50 }
      ],
      separation_points: [
        {
          id: "sp-hvac",
          name: "Rooftop HVAC Chiller Unit",
          x: targetEquipment.x,
          y: targetEquipment.z,
          z: buildingHeight,
          associated_node_id: "node-c1",
          insulation_medium: "air",
          physical_distance_m: physicalClearance
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
      setCalcResult(data[0])

      // Nodal Current-Sharing calculation
      const nodalRes = await fetch('http://localhost:8000/api/v1/calculations/nodal-kc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodes: payload.nodes,
          segments: payload.segments,
          injection_node: "node-c1",
          earth_nodes: ["earth-1", "earth-2", "earth-3", "earth-4"]
        })
      })
      const nData = await nodalRes.json()
      setNodalResult(nData.kc_factors)
    } catch (e) {
      console.error("Calculation error:", e)
    }
  }

  // Export PDF Report
  const downloadPdfReport = async () => {
    const payload = {
      name: `AegisLPS Engineering Project - Class ${lpsClass}`,
      lps_class: lpsClass,
      building: { length_m: buildingLength, width_m: buildingWidth, height_m: buildingHeight, roof_type: "flat" },
      nodes: [{ id: "n1", x: 0, y: 0, z: buildingHeight, node_type: "air_termination" }],
      segments: [],
      separation_points: [{
        id: "sp-hvac",
        name: "Rooftop HVAC Unit",
        x: targetEquipment.x,
        y: targetEquipment.z,
        z: buildingHeight,
        associated_node_id: "n1",
        insulation_medium: "air",
        physical_distance_m: physicalClearance
      }]
    }

    const res = await fetch('http://localhost:8000/api/v1/reports/pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `AegisLPS_Report_Class_${lpsClass}.pdf`
    a.click()
  }

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', background: '#090d16', color: '#f8fafc', fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Engineering Control Panel */}
      <div style={{ width: '420px', padding: '24px', backgroundColor: '#111827', borderRight: '1px solid #1f2937', overflowY: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <h2 style={{ color: '#38bdf8', margin: 0, fontSize: '20px', letterSpacing: '-0.02em' }}>AegisLPS Modeller</h2>
          <span style={{ fontSize: '11px', background: '#0369a1', padding: '2px 8px', borderRadius: '12px', fontWeight: 'bold' }}>PROTOTYPE</span>
        </div>
        <p style={{ fontSize: '12px', color: '#9ca3af', marginTop: 0, marginBottom: '20px' }}>
          IEC 62305-3:2024 Advanced Nodal & 3D Separation Distance Toolbox
        </p>

        {/* Camera Views */}
        <div style={{ marginBottom: '18px', padding: '12px', background: '#1f2937', borderRadius: '6px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#e5e7eb', display: 'block', marginBottom: '8px', textTransform: 'uppercase' }}>Camera Preset:</span>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
            {(['iso', 'top', 'front', 'side'] as const).map(view => (
              <button
                key={view}
                onClick={() => setCameraView(view)}
                style={{
                  padding: '6px 0',
                  background: cameraView === view ? '#0284c7' : '#374151',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  fontWeight: 600,
                  fontSize: '11px',
                  cursor: 'pointer',
                  textTransform: 'uppercase'
                }}
              >
                {view}
              </button>
            ))}
          </div>
        </div>

        {/* 3D Visualization Layers */}
        <div style={{ marginBottom: '18px', padding: '12px', background: '#1f2937', borderRadius: '6px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#e5e7eb', display: 'block', marginBottom: '8px', textTransform: 'uppercase' }}>Engineering Layers:</span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input type="checkbox" checked={showBuilding} onChange={e => setShowBuilding(e.target.checked)} /> Structure Shell
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input type="checkbox" checked={showMeshGrid} onChange={e => setShowMeshGrid(e.target.checked)} /> Roof Mesh Grid
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input type="checkbox" checked={showRods} onChange={e => setShowRods(e.target.checked)} /> Air Terminations
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input type="checkbox" checked={showDownConductors} onChange={e => setShowDownConductors(e.target.checked)} /> Down Conductors
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input type="checkbox" checked={showSpherePenetration} onChange={e => setShowSpherePenetration(e.target.checked)} /> Sphere Envelope (R={sphereRadius}m)
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input type="checkbox" checked={showCurrentHeatmap} onChange={e => setShowCurrentHeatmap(e.target.checked)} /> Current (kc) Heatmap
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input type="checkbox" checked={showEquipment} onChange={e => setShowEquipment(e.target.checked)} /> Rooftop Objects
            </label>
          </div>
        </div>

        {/* Parameters */}
        <div style={{ marginBottom: '14px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>LPS Protection Class:</label>
          <select value={lpsClass} onChange={e => setLpsClass(e.target.value as any)} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1f2937', color: '#fff', border: '1px solid #374151', fontSize: '13px' }}>
            <option value="I">Class I (ki = 0.08, R = 20m)</option>
            <option value="II">Class II (ki = 0.06, R = 30m)</option>
            <option value="III">Class III/IV (ki = 0.04, R = 45m)</option>
          </select>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Length (m):</label>
            <input type="number" value={buildingLength} onChange={e => setBuildingLength(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1f2937', color: '#fff', border: '1px solid #374151', fontSize: '13px' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Width (m):</label>
            <input type="number" value={buildingWidth} onChange={e => setBuildingWidth(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1f2937', color: '#fff', border: '1px solid #374151', fontSize: '13px' }} />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '18px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Height (m):</label>
            <input type="number" value={buildingHeight} onChange={e => setBuildingHeight(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1f2937', color: '#fff', border: '1px solid #374151', fontSize: '13px' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Air Clearance (m):</label>
            <input type="number" step="0.1" value={physicalClearance} onChange={e => setPhysicalClearance(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1f2937', color: '#fff', border: '1px solid #374151', fontSize: '13px' }} />
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <button onClick={runEngineeringCalculations} style={{ padding: '12px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', fontSize: '13px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            Calculate Compliance & Current Sharing
          </button>
          <button onClick={downloadPdfReport} style={{ padding: '10px', backgroundColor: '#374151', color: '#fff', border: '1px solid #4b5563', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', fontSize: '12px' }}>
            Export Audit PDF Report
          </button>
        </div>

        {/* Calculation Result Feedback */}
        {calcResult && (
          <div style={{ marginTop: '20px', padding: '16px', backgroundColor: calcResult.pass_compliance ? 'rgba(6, 78, 59, 0.4)' : 'rgba(127, 29, 29, 0.4)', border: `1px solid ${calcResult.pass_compliance ? '#10b981' : '#ef4444'}`, borderRadius: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 'bold', color: calcResult.pass_compliance ? '#34d399' : '#f87171' }}>
                {calcResult.pass_compliance ? 'COMPLIANT (PASS)' : 'NON-COMPLIANT (VIOLATION)'}
              </span>
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>IEC 62305-3 §6.3</span>
            </div>
            <div style={{ fontSize: '12px', lineHeight: '1.6' }}>
              <div><b>Required Separation (s):</b> {calcResult.required_distance_s_m.toFixed(3)} m</div>
              <div><b>Actual Physical Clearance:</b> {calcResult.actual_distance_m.toFixed(3)} m</div>
              <div><b>Engineering Safety Margin:</b> {calcResult.safety_margin_m > 0 ? '+' : ''}{calcResult.safety_margin_m.toFixed(3)} m</div>
            </div>
            <div style={{ marginTop: '10px', padding: '8px', background: '#0f172a', borderRadius: '4px', fontSize: '11px', fontFamily: 'monospace', color: '#cbd5e1' }}>
              {calcResult.formula_trace}
            </div>
          </div>
        )}
      </div>

      {/* 3D WebGL Interactive Canvas */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas camera={{ position: getCameraPos(), fov: 45 }}>
          <ambientLight intensity={0.8} />
          <directionalLight position={[30, 50, 30]} intensity={1.5} />
          <Grid args={[100, 100]} cellColor="#1f2937" sectionColor="#0284c7" />
          <OrbitControls />

          {/* Building Shell */}
          {showBuilding && (
            <mesh position={[0, buildingHeight / 2, 0]}>
              <boxGeometry args={[buildingLength, buildingHeight, buildingWidth]} />
              <meshStandardMaterial color="#1e293b" opacity={0.7} transparent />
            </mesh>
          )}

          {/* Air Termination Roof Mesh Grid */}
          {showMeshGrid && (
            <group position={[0, buildingHeight + 0.05, 0]}>
              {/* Perimeter Ring Conductor */}
              <Line
                points={[
                  [-buildingLength / 2, 0, -buildingWidth / 2],
                  [buildingLength / 2, 0, -buildingWidth / 2],
                  [buildingLength / 2, 0, buildingWidth / 2],
                  [-buildingLength / 2, 0, buildingWidth / 2],
                  [-buildingLength / 2, 0, -buildingWidth / 2]
                ]}
                color="#eab308"
                lineWidth={3}
              />
              {/* Internal Mesh Lines */}
              <Line
                points={[
                  [-buildingLength / 2, 0, 0],
                  [buildingLength / 2, 0, 0]
                ]}
                color="#ca8a04"
                lineWidth={1.5}
              />
              <Line
                points={[
                  [0, 0, -buildingWidth / 2],
                  [0, 0, buildingWidth / 2]
                ]}
                color="#ca8a04"
                lineWidth={1.5}
              />
            </group>
          )}

          {/* Air Termination Rods */}
          {showRods && rods.map(rod => (
            <group key={rod.id} position={[rod.x, rod.y, rod.z]}>
              <mesh position={[0, rodHeight / 2, 0]}>
                <cylinderGeometry args={[0.04, 0.06, rodHeight]} />
                <meshStandardMaterial color="#f59e0b" roughness={0.3} metalness={0.8} />
              </mesh>
              {/* Tip Contact Indicator */}
              <mesh position={[0, rodHeight, 0]}>
                <sphereGeometry args={[0.15, 16, 16]} />
                <meshStandardMaterial color="#ef4444" />
              </mesh>
            </group>
          ))}

          {/* Down Conductors & Current Heatmap */}
          {showDownConductors && downConductors.map((dc, i) => {
            const kcValue = nodalResult ? (nodalResult[`seg-dc${i + 1}`] || 0.25) : 0.25
            const segColor = showCurrentHeatmap
              ? (kcValue > 0.4 ? '#ef4444' : kcValue > 0.2 ? '#f59e0b' : '#10b981')
              : '#38bdf8'

            return (
              <group key={dc.id} position={[dc.x, 0, dc.z]}>
                <mesh position={[0, buildingHeight / 2, 0]}>
                  <cylinderGeometry args={[0.05, 0.05, buildingHeight]} />
                  <meshStandardMaterial color={segColor} roughness={0.4} metalness={0.6} />
                </mesh>
                {/* Earth Termination Electrode Marker */}
                <mesh position={[0, -0.5, 0]}>
                  <cylinderGeometry args={[0.12, 0.12, 1.0]} />
                  <meshStandardMaterial color="#64748b" />
                </mesh>
              </group>
            )
          })}

          {/* Rolling Sphere Protection Envelope (Inter-rod Sagitta Penetration Surface) */}
          {showSpherePenetration && (
            <mesh position={[0, buildingHeight + rodHeight - sphereRadius * 0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
              <ringGeometry args={[0, Math.min(buildingLength, buildingWidth) * 0.7, 32]} />
              <meshStandardMaterial color="#38bdf8" opacity={0.15} transparent wireframe />
            </mesh>
          )}

          {/* Rooftop Installation / Target Equipment */}
          {showEquipment && (
            <group position={[targetEquipment.x, targetEquipment.y, targetEquipment.z]}>
              <mesh>
                <boxGeometry args={targetEquipment.size} />
                <meshStandardMaterial color="#475569" roughness={0.5} />
              </mesh>
              {/* Clearance Vector from Equipment to Conductor */}
              {calcResult && (
                <Line
                  points={[
                    [0, 0, 0],
                    [-4.0, 0, -3.0]
                  ]}
                  color={calcResult.pass_compliance ? '#10b981' : '#ef4444'}
                  lineWidth={3}
                  dashed
                />
              )}
            </group>
          )}
        </Canvas>
      </div>
    </div>
  )
}
