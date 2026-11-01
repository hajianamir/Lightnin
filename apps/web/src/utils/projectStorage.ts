/**
 * Project Serialization, Local PC File I/O, and LocalStorage Caching Utility.
 */

export interface AegisProjectFile {
  schema_version: string
  application_version: string
  standards_baseline: string
  project_id: string
  name: string
  lps_class: 'I' | 'II' | 'III' | 'IV'
  building: {
    length_m: number
    width_m: number
    height_m: number
    roof_type: string
  }
  soil_resistivity_ohm_m: number
  physical_clearance_m: number
  created_at: string
  updated_at: string
}

export function exportProjectToFile(project: AegisProjectFile) {
  const jsonStr = JSON.stringify(project, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${project.name.replace(/[^a-zA-Z0-9_-]/g, '_')}_${project.project_id.slice(0, 8)}.lps`
  a.click()
  URL.revokeObjectURL(url)
}

export function loadProjectFromFile(file: File): Promise<AegisProjectFile> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const parsed = JSON.parse(e.target?.result as string)
        if (!parsed.building || !parsed.lps_class) {
          throw new Error('Invalid AegisLPS project file: Missing required building or LPS class attributes.')
        }
        resolve(parsed as AegisProjectFile)
      } catch (err) {
        reject(err)
      }
    }
    reader.onerror = () => reject(new Error('Failed to read file from disk.'))
    reader.readAsText(file)
  })
}

export function saveProjectToLocalStorage(project: AegisProjectFile) {
  try {
    localStorage.setItem('aegislps_active_project', JSON.stringify(project))
  } catch (e) {
    console.error('LocalStorage save error:', e)
  }
}

export function loadProjectFromLocalStorage(): AegisProjectFile | null {
  try {
    const data = localStorage.getItem('aegislps_active_project')
    if (data) {
      return JSON.parse(data)
    }
  } catch (e) {
    console.error('LocalStorage load error:', e)
  }
  return null
}
