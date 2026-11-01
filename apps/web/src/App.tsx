import { useState, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Grid, Line } from '@react-three/drei'

export default function App() {
  // Navigation & Workspace Tabs
  const [activeTab, setActiveTab] = useState<'3d' | '2d' | 'separation' | 'nodal' | 'earthing' | 'uq' | 'risk'>('3d')

  // Engineering Parameters
  const [lpsClass, setLpsClass] = useState<'I' | 'II' | 'III'>('I')
  const [buildingLength, setBuildingLength] = useState(30)
  const [buildingWidth, setBuildingWidth] = useState(20)
  const [buildingHeight, setBuildingHeight] = useState(15)
  const [physicalClearance, setPhysicalClearance] = useState(1.1)
  const [soilResistivity, setSoilResistivity] = useState(100.0)

  // 3D Viewport Controls & Layer States
  const [cameraView, setCameraView] = useState<'iso' | 'top' | 'front' | 'side'>('iso')
  const [showBuilding, setShowBuilding] = useState(true)
  const [showMeshGrid, setShowMeshGrid] = useState(true)
  const [showRods, setShowRods] = useState(true)
  const [showDownConductors, setShowDownConductors] = useState(true)
  const [showSpherePenetration, setShowSpherePenetration] = useState(true)
  const [showCurrentHeatmap, setShowCurrentHeatmap] = useState(true)
  const [showEquipment] = useState(true)

  // Calculation Results
  const [calcResult, setCalcResult] = useState<any>(null)
  const [nodalResult, setNodalResult] = useState<any>(null)
  const [earthingResult, setEarthingResult] = useState<any>(null)
  const [uqResult, setUqResult] = useState<any>(null)

  // Rolling sphere radius per IEC 62305-3:2024 Table 2
  const sphereRadius = useMemo(() => {
    switch (lpsClass) {
      case 'I': return 20.0
      case 'II': return 30.0
      case 'III': return 45.0
      default: return 20.0
    }
  }, [lpsClass])

  const rodHeight = 3.0
  const rods = useMemo(() => [
    { id: 'rod-1', x: -buildingLength / 3, y: buildingHeight, z: -buildingWidth / 3 },
    { id: 'rod-2', x: buildingLength / 3, y: buildingHeight, z: -buildingWidth / 3 },
    { id: 'rod-3', x: buildingLength / 3, y: buildingHeight, z: buildingWidth / 3 },
    { id: 'rod-4', x: -buildingLength / 3, y: buildingHeight, z: buildingWidth / 3 },
    { id: 'rod-center', x: 0, y: buildingHeight, z: 0 },
  ], [buildingLength, buildingWidth, buildingHeight])

  const downConductors = useMemo(() => [
    { id: 'dc-1', x: -buildingLength / 2, z: -buildingWidth / 2 },
    { id: 'dc-2', x: buildingLength / 2, z: -buildingWidth / 2 },
    { id: 'dc-3', x: buildingLength / 2, z: buildingWidth / 2 },
    { id: 'dc-4', x: -buildingLength / 2, z: buildingWidth / 2 },
  ], [buildingLength, buildingWidth])

  const targetEquipment = {
    x: 4.0,
    y: buildingHeight + 1.2,
    z: 3.0,
    size: [2.5, 2.0, 2.0] as [number, number, number]
  }

  const getCameraPos = (): [number, number, number] => {
    switch (cameraView) {
      case 'top': return [0, buildingHeight + 50, 0.001]
      case 'front': return [0, buildingHeight / 2, buildingWidth + 40]
      case 'side': return [buildingLength + 40, buildingHeight / 2, 0]
      default: return [35, buildingHeight + 25, 35]
    }
  }

  const runAllCalculations = async () => {
    try {
      // 1. Separation Distance
      const sepPayload = {
        name: `Facility L${lpsClass}`,
        lps_class: lpsClass,
        building: { length_m: buildingLength, width_m: buildingWidth, height_m: buildingHeight, roof_type: "flat" },
        nodes: [{ id: "n1", x: 0, y: 0, z: buildingHeight, node_type: "air_termination" }],
        segments: [],
        separation_points: [{
          id: "sp-hvac",
          name: "Rooftop HVAC Unit",
          x: targetEquipment.x, y: targetEquipment.z, z: buildingHeight,
          associated_node_id: "n1",
          insulation_medium: "air",
          physical_distance_m: physicalClearance
        }]
      }
      const sepRes = await fetch('http://localhost:8000/api/v1/calculations/separation-distance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sepPayload)
      })
      const sepData = await sepRes.json()
      setCalcResult(sepData[0])

      // 2. Nodal Current Sharing
      const nodalRes = await fetch('http://localhost:8000/api/v1/calculations/nodal-kc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodes: [
            { id: "c1", x: downConductors[0].x, y: downConductors[0].z, z: buildingHeight },
            { id: "c2", x: downConductors[1].x, y: downConductors[1].z, z: buildingHeight },
            { id: "e1", x: downConductors[0].x, y: downConductors[0].z, z: 0 },
            { id: "e2", x: downConductors[1].x, y: downConductors[1].z, z: 0 }
          ],
          segments: [
            {"id": "seg-dc1", "start_node_id": "c1", "end_node_id": "e1"},
            {"id": "seg-dc2", "start_node_id": "c2", "end_node_id": "e2"}
          ],
          injection_node: "c1",
          earth_nodes: ["e1", "e2"]
        })
      })
      const nData = await nodalRes.json()
      setNodalResult(nData)

      // 3. Earthing Analysis (Dwight Ring)
      const earthRes = await fetch('http://localhost:8000/api/v1/calculations/earthing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lps_class: lpsClass,
          soil: { is_two_layer: false, rho_upper_ohm_m: soilResistivity },
          electrode_type: "type_b_ring",
          ring_radius_m: 15.0
        })
      })
      const eData = await earthRes.json()
      setEarthingResult(eData)

      // 4. Uncertainty Quantification (UQ Monte Carlo)
      const uqRes = await fetch('http://localhost:8000/api/v1/calculations/uq-monte-carlo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_samples: 1500,
          lps_class: lpsClass,
          target_clearance_d_m: physicalClearance,
          nominal_path_length_m: buildingHeight,
          nominal_soil_rho_ohm_m: soilResistivity
        })
      })
      const uData = await uqRes.json()
      setUqResult(uData)
    } catch (err) {
      console.error("Calculation execution failed:", err)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', background: '#0a0f1d', color: '#f1f5f9', fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Top Professional Header & Workspace Nav */}
      <header style={{ height: '54px', borderBottom: '1px solid #1e293b', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 20px', background: '#0d1527' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '18px', fontWeight: 800, color: '#38bdf8', letterSpacing: '-0.03em' }}>AegisLPS</span>
          <span style={{ fontSize: '11px', color: '#94a3b8', borderLeft: '1px solid #334155', paddingLeft: '12px' }}>
            IEC 62305:2024 Engineering Suite
          </span>
          <span style={{ background: '#0369a1', color: '#fff', fontSize: '10px', padding: '2px 8px', borderRadius: '10px', fontWeight: 700 }}>v1.0.0-alpha.1</span>
        </div>

        {/* Workspace Mode Tabs */}
        <div style={{ display: 'flex', gap: '4px' }}>
          {[
            { id: '3d', label: '3D Modeller' },
            { id: '2d', label: '2D CAD Plan' },
            { id: 'separation', label: 'Separation (s)' },
            { id: 'nodal', label: 'Nodal (kc)' },
            { id: 'earthing', label: 'Earthing & Potentials' },
            { id: 'uq', label: 'UQ & Sensitivity' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: '7px 14px',
                borderRadius: '6px',
                border: 'none',
                background: activeTab === tab.id ? '#0284c7' : 'transparent',
                color: activeTab === tab.id ? '#fff' : '#94a3b8',
                fontWeight: 600,
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <button
          onClick={runAllCalculations}
          style={{
            padding: '8px 16px',
            background: '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 700,
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >
          Compute All Solvers
        </button>
      </header>

      {/* Main Workspace Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Side Parameters Inspector */}
        <aside style={{ width: '380px', background: '#0d1527', borderRight: '1px solid #1e293b', padding: '20px', overflowY: 'auto' }}>
          <h3 style={{ fontSize: '13px', textTransform: 'uppercase', color: '#38bdf8', letterSpacing: '0.05em', marginTop: 0 }}>
            Project Engineering Parameters
          </h3>

          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>LPS Protection Class:</label>
            <select value={lpsClass} onChange={e => setLpsClass(e.target.value as any)} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1e293b', color: '#fff', border: '1px solid #334155', fontSize: '13px' }}>
              <option value="I">Class I (ki = 0.08, R = 20m)</option>
              <option value="II">Class II (ki = 0.06, R = 30m)</option>
              <option value="III">Class III/IV (ki = 0.04, R = 45m)</option>
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Length L (m):</label>
              <input type="number" value={buildingLength} onChange={e => setBuildingLength(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1e293b', color: '#fff', border: '1px solid #334155', fontSize: '13px' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Width W (m):</label>
              <input type="number" value={buildingWidth} onChange={e => setBuildingWidth(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1e293b', color: '#fff', border: '1px solid #334155', fontSize: '13px' }} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Height H (m):</label>
              <input type="number" value={buildingHeight} onChange={e => setBuildingHeight(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1e293b', color: '#fff', border: '1px solid #334155', fontSize: '13px' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Air Clearance (m):</label>
              <input type="number" step="0.1" value={physicalClearance} onChange={e => setPhysicalClearance(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1e293b', color: '#fff', border: '1px solid #334155', fontSize: '13px' }} />
            </div>
          </div>

          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Soil Resistivity (ohm.m):</label>
            <input type="number" value={soilResistivity} onChange={e => setSoilResistivity(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#1e293b', color: '#fff', border: '1px solid #334155', fontSize: '13px' }} />
          </div>

          {/* 3D Camera & Layer Controls */}
          {activeTab === '3d' && (
            <div style={{ background: '#1e293b', padding: '12px', borderRadius: '6px', marginBottom: '16px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', display: 'block', marginBottom: '8px', textTransform: 'uppercase' }}>Camera Presets:</span>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px', marginBottom: '12px' }}>
                {(['iso', 'top', 'front', 'side'] as const).map(view => (
                  <button
                    key={view}
                    onClick={() => setCameraView(view)}
                    style={{
                      padding: '5px 0',
                      background: cameraView === view ? '#0284c7' : '#334155',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '4px',
                      fontWeight: 600,
                      fontSize: '10px',
                      cursor: 'pointer',
                      textTransform: 'uppercase'
                    }}
                  >
                    {view}
                  </button>
                ))}
              </div>

              <span style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', display: 'block', marginBottom: '6px', textTransform: 'uppercase' }}>Layers:</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '11px' }}>
                <label><input type="checkbox" checked={showBuilding} onChange={e => setShowBuilding(e.target.checked)} /> Structure</label>
                <label><input type="checkbox" checked={showMeshGrid} onChange={e => setShowMeshGrid(e.target.checked)} /> Mesh Grid</label>
                <label><input type="checkbox" checked={showRods} onChange={e => setShowRods(e.target.checked)} /> Air Terminations</label>
                <label><input type="checkbox" checked={showDownConductors} onChange={e => setShowDownConductors(e.target.checked)} /> Down Conductors</label>
                <label><input type="checkbox" checked={showSpherePenetration} onChange={e => setShowSpherePenetration(e.target.checked)} /> Sphere Envelope</label>
                <label><input type="checkbox" checked={showCurrentHeatmap} onChange={e => setShowCurrentHeatmap(e.target.checked)} /> Current (kc) Map</label>
              </div>
            </div>
          )}

          {/* Quick Result Badge */}
          {calcResult && (
            <div style={{ padding: '12px', borderRadius: '6px', background: calcResult.pass_compliance ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', border: `1px solid ${calcResult.pass_compliance ? '#10b981' : '#ef4444'}` }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: calcResult.pass_compliance ? '#34d399' : '#f87171' }}>
                {calcResult.pass_compliance ? 'COMPLIANT (PASS)' : 'VIOLATION DETECTED'}
              </span>
              <div style={{ fontSize: '11px', marginTop: '4px' }}>Req: {calcResult.required_distance_s_m.toFixed(3)}m | Margin: {calcResult.safety_margin_m.toFixed(3)}m</div>
            </div>
          )}
        </aside>

        {/* Center Dynamic Workspace Area */}
        <main style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          {activeTab === '3d' && (
            <Canvas camera={{ position: getCameraPos(), fov: 45 }}>
              <ambientLight intensity={0.8} />
              <directionalLight position={[30, 50, 30]} intensity={1.5} />
              <Grid args={[100, 100]} cellColor="#1e293b" sectionColor="#0284c7" />
              <OrbitControls />

              {showBuilding && (
                <mesh position={[0, buildingHeight / 2, 0]}>
                  <boxGeometry args={[buildingLength, buildingHeight, buildingWidth]} />
                  <meshStandardMaterial color="#1e293b" opacity={0.7} transparent />
                </mesh>
              )}

              {showMeshGrid && (
                <group position={[0, buildingHeight + 0.05, 0]}>
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
                </group>
              )}

              {showRods && rods.map(rod => (
                <group key={rod.id} position={[rod.x, rod.y, rod.z]}>
                  <mesh position={[0, rodHeight / 2, 0]}>
                    <cylinderGeometry args={[0.04, 0.06, rodHeight]} />
                    <meshStandardMaterial color="#f59e0b" roughness={0.3} metalness={0.8} />
                  </mesh>
                  <mesh position={[0, rodHeight, 0]}>
                    <sphereGeometry args={[0.15, 16, 16]} />
                    <meshStandardMaterial color="#ef4444" />
                  </mesh>
                </group>
              ))}

              {showDownConductors && downConductors.map((dc, i) => {
                const segColor = showCurrentHeatmap ? (i % 2 === 0 ? '#38bdf8' : '#10b981') : '#38bdf8'
                return (
                  <group key={dc.id} position={[dc.x, 0, dc.z]}>
                    <mesh position={[0, buildingHeight / 2, 0]}>
                      <cylinderGeometry args={[0.05, 0.05, buildingHeight]} />
                      <meshStandardMaterial color={segColor} roughness={0.4} metalness={0.6} />
                    </mesh>
                    <mesh position={[0, -0.5, 0]}>
                      <cylinderGeometry args={[0.12, 0.12, 1.0]} />
                      <meshStandardMaterial color="#64748b" />
                    </mesh>
                  </group>
                )
              })}

              {showSpherePenetration && (
                <mesh position={[0, buildingHeight + rodHeight - sphereRadius * 0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
                  <ringGeometry args={[0, Math.min(buildingLength, buildingWidth) * 0.7, 32]} />
                  <meshStandardMaterial color="#38bdf8" opacity={0.15} transparent wireframe />
                </mesh>
              )}

              {showEquipment && (
                <group position={[targetEquipment.x, targetEquipment.y, targetEquipment.z]}>
                  <mesh>
                    <boxGeometry args={targetEquipment.size} />
                    <meshStandardMaterial color="#475569" roughness={0.5} />
                  </mesh>
                  {calcResult && (
                    <Line
                      points={[[0, 0, 0], [-4.0, 0, -3.0]]}
                      color={calcResult.pass_compliance ? '#10b981' : '#ef4444'}
                      lineWidth={3}
                      dashed
                    />
                  )}
                </group>
              )}
            </Canvas>
          )}

          {/* 2D CAD Plan View */}
          {activeTab === '2d' && (
            <div style={{ padding: '30px', height: '100%', overflowY: 'auto' }}>
              <h2 style={{ fontSize: '18px', color: '#38bdf8', marginTop: 0 }}>2D Technical CAD Layout (Plan View)</h2>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>Top-down orthographic representation with coordinate grid and conductors</p>

              <div style={{ width: '560px', height: '380px', border: '1px solid #334155', position: 'relative', background: '#070b14', borderRadius: '8px', margin: '20px 0' }}>
                {/* Building Perimeter */}
                <div style={{ position: 'absolute', left: '80px', top: '60px', width: '400px', height: '260px', border: '2px solid #eab308' }}>
                  <span style={{ position: 'absolute', top: '-18px', left: '10px', fontSize: '10px', color: '#eab308' }}>Roof Ring Conductor</span>
                  {/* Down Conductors at 4 corners */}
                  <div style={{ position: 'absolute', top: '-5px', left: '-5px', width: '10px', height: '10px', borderRadius: '50%', background: '#38bdf8' }} title="Down Conductor 1" />
                  <div style={{ position: 'absolute', top: '-5px', right: '-5px', width: '10px', height: '10px', borderRadius: '50%', background: '#38bdf8' }} title="Down Conductor 2" />
                  <div style={{ position: 'absolute', bottom: '-5px', right: '-5px', width: '10px', height: '10px', borderRadius: '50%', background: '#38bdf8' }} title="Down Conductor 3" />
                  <div style={{ position: 'absolute', bottom: '-5px', left: '-5px', width: '10px', height: '10px', borderRadius: '50%', background: '#38bdf8' }} title="Down Conductor 4" />

                  {/* Rooftop HVAC Target */}
                  <div style={{ position: 'absolute', left: '160px', top: '100px', width: '40px', height: '40px', background: '#475569', border: '1px dashed #ef4444' }}>
                    <span style={{ fontSize: '9px', color: '#fff', padding: '2px' }}>HVAC</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* UQ (Uncertainty Quantification) Dashboard Tab */}
          {activeTab === 'uq' && (
            <div style={{ padding: '30px', height: '100%', overflowY: 'auto' }}>
              <h2 style={{ fontSize: '18px', color: '#38bdf8', marginTop: 0 }}>Uncertainty Quantification & Global Sensitivity Analysis</h2>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>
                Stochastic Monte Carlo simulation (1,500 samples) under geotechnical and parametric uncertainty
              </p>

              {uqResult ? (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', margin: '20px 0' }}>
                    <div style={{ background: '#1e293b', padding: '15px', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>Median Required (P50)</span>
                      <div style={{ fontSize: '20px', fontWeight: 800, color: '#38bdf8' }}>{uqResult.p50_median_s_m} m</div>
                    </div>
                    <div style={{ background: '#1e293b', padding: '15px', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>95% Confidence (P95)</span>
                      <div style={{ fontSize: '20px', fontWeight: 800, color: '#f59e0b' }}>{uqResult.p95_s_m} m</div>
                    </div>
                    <div style={{ background: '#1e293b', padding: '15px', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>99% Upper Bound (P99)</span>
                      <div style={{ fontSize: '20px', fontWeight: 800, color: '#ef4444' }}>{uqResult.p99_s_m} m</div>
                    </div>
                    <div style={{ background: '#1e293b', padding: '15px', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>Probability of Violation</span>
                      <div style={{ fontSize: '20px', fontWeight: 800, color: uqResult.probability_of_violation_pct < 5 ? '#10b981' : '#ef4444' }}>
                        {uqResult.probability_of_violation_pct}%
                      </div>
                    </div>
                  </div>

                  {/* Sobol Sensitivity Indices Bar Display */}
                  <div style={{ background: '#1e293b', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
                    <h4 style={{ margin: '0 0 14px 0', fontSize: '13px', color: '#e2e8f0' }}>Sobol First-Order Sensitivity Indices (S_i)</h4>
                    {Object.entries(uqResult.sobol_first_order_indices).map(([param, val]: any) => (
                      <div key={param} style={{ marginBottom: '10px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                          <span>{param}</span>
                          <span style={{ fontWeight: 700 }}>{(val * 100).toFixed(1)}%</span>
                        </div>
                        <div style={{ width: '100%', height: '8px', background: '#0f172a', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ width: `${val * 100}%`, height: '100%', background: '#38bdf8' }} />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Engineering Insights */}
                  <div style={{ background: '#0f172a', padding: '16px', borderRadius: '8px', border: '1px solid #1e293b' }}>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#38bdf8', textTransform: 'uppercase' }}>UQ Diagnostics & Insights:</h4>
                    {uqResult.engineering_insights.map((msg: string, i: number) => (
                      <p key={i} style={{ fontSize: '12px', color: '#cbd5e1', margin: '4px 0' }}>• {msg}</p>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                  Click "Compute All Solvers" in the header to run the stochastic UQ simulation.
                </div>
              )}
            </div>
          )}

          {/* Nodal Tab */}
          {activeTab === 'nodal' && (
            <div style={{ padding: '30px', height: '100%', overflowY: 'auto' }}>
              <h2 style={{ fontSize: '18px', color: '#38bdf8', marginTop: 0 }}>Nodal Current-Sharing & Branch Results</h2>
              {nodalResult ? (
                <div style={{ background: '#1e293b', padding: '20px', borderRadius: '8px', marginTop: '16px' }}>
                  <div>Status: <b>{nodalResult.converged ? 'CONVERGED' : 'WARNING'}</b></div>
                  <div>Balance Residual: <b>{nodalResult.conservation_residual_a || 0} A</b></div>
                  <pre style={{ background: '#0f172a', padding: '12px', borderRadius: '6px', fontSize: '12px', color: '#38bdf8', marginTop: '14px' }}>
                    {JSON.stringify(nodalResult.kc_factors, null, 2)}
                  </pre>
                </div>
              ) : (
                <div style={{ padding: '20px', color: '#94a3b8' }}>Run 'Compute All Solvers' to view nodal branch currents.</div>
              )}
            </div>
          )}

          {/* Separation Distance Detailed Tab */}
          {activeTab === 'separation' && (
            <div style={{ padding: '30px', height: '100%', overflowY: 'auto' }}>
              <h2 style={{ fontSize: '18px', color: '#38bdf8', marginTop: 0 }}>IEC 62305-3 §6.3 Separation Distance Engine</h2>
              {calcResult && (
                <div style={{ background: '#1e293b', padding: '20px', borderRadius: '8px', marginTop: '16px' }}>
                  <div style={{ fontSize: '14px', marginBottom: '8px' }}>
                    <b>Compliance Status:</b> <span style={{ color: calcResult.pass_compliance ? '#10b981' : '#ef4444', fontWeight: 800 }}>{calcResult.pass_compliance ? 'PASS' : 'FAIL'}</span>
                  </div>
                  <div>Required Distance (s): <b>{calcResult.required_distance_s_m.toFixed(4)} m</b></div>
                  <div>Actual Physical Clearance: <b>{calcResult.actual_distance_m.toFixed(4)} m</b></div>
                  <div>Safety Margin: <b>{calcResult.safety_margin_m > 0 ? '+' : ''}{calcResult.safety_margin_m.toFixed(4)} m</b></div>
                  <pre style={{ background: '#0f172a', padding: '12px', borderRadius: '6px', fontSize: '12px', color: '#38bdf8', marginTop: '14px' }}>
                    {calcResult.formula_trace}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* Earthing Analysis Tab */}
          {activeTab === 'earthing' && (
            <div style={{ padding: '30px', height: '100%', overflowY: 'auto' }}>
              <h2 style={{ fontSize: '18px', color: '#38bdf8', marginTop: 0 }}>Earthing System & Potential Assessment</h2>
              {earthingResult && (
                <div style={{ background: '#1e293b', padding: '20px', borderRadius: '8px', marginTop: '16px' }}>
                  <div style={{ fontSize: '14px', marginBottom: '8px' }}>
                    <b>Status:</b> <span style={{ color: earthingResult.meets_recommended_10_ohm ? '#10b981' : '#f59e0b', fontWeight: 800 }}>{earthingResult.status}</span>
                  </div>
                  <div>Stationary Resistance (R_dc): <b>{earthingResult.stationary_resistance_r_ohm} ohm</b></div>
                  <div>Impulse Impedance (Z_imp): <b>{earthingResult.impulse_impedance_z_ohm} ohm</b></div>
                  <div>Effective Electrode Length: <b>{earthingResult.actual_effective_length_m} m</b> (Min IEC l1: {earthingResult.minimum_length_l1_m} m)</div>
                  <pre style={{ background: '#0f172a', padding: '12px', borderRadius: '6px', fontSize: '12px', color: '#38bdf8', marginTop: '14px' }}>
                    {earthingResult.method_details}
                  </pre>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
