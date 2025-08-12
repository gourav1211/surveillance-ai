import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { useToast } from './ToastContext'

const DetectionContext = createContext()

export function useDetection() {
  const context = useContext(DetectionContext)
  if (!context) {
    throw new Error('useDetection must be used within a DetectionProvider')
  }
  return context
}

export function DetectionProvider({ children }) {
  const [currentDetection, setCurrentDetection] = useState(null)
  const [detectionHistory, setDetectionHistory] = useState([])
  const [isDetecting, setIsDetecting] = useState(false)
  const [detectionCount, setDetectionCount] = useState(0)
  const { showError, showWarning, showInfo } = useToast()

  const updateDetection = useCallback((detectionData) => {
    if (!detectionData) return

    // Extract current active count and new arrivals separately
    const activePersonCount = detectionData.person_count || 0  // Current people in frame
    const newArrivals = detectionData.new_person_count || 0    // Only new people in this event
    
    const newDetection = {
      id: Date.now(),
      timestamp: Date.now(),
      personCount: activePersonCount,  // Display current active count
      newPersonCount: newArrivals,     // Track new arrivals
      objectTypes: detectionData.detections?.objects || ['person'], // Support multiple object types
      boxes: detectionData.detections?.boxes || [],
      severity: detectionData.severity || 'medium',
      isActive: true
    }

    setCurrentDetection(newDetection)
    // Only increment by NEW arrivals, not total active count
    setDetectionCount(prev => prev + newArrivals)
    
    // Add to history
    setDetectionHistory(prev => [newDetection, ...prev.slice(0, 49)]) // Keep last 50
    
    // Show appropriate notification based on object types and severity
    const hasWeapon = newDetection.objectTypes.includes('weapon')
    const activeCount = newDetection.personCount
    const newCount = newDetection.newPersonCount
    
    if (hasWeapon || detectionData.severity === 'critical') {
      showError(`🚨 ${detectionData.title || 'Critical Alert Detected!'}`, 5000)
    } else if (activeCount > 2 || detectionData.severity === 'high') {
      showWarning(`⚠️ ${detectionData.title || `${newCount} new, ${activeCount} total persons detected`}`, 4000)
    } else if (newCount > 0) {
      showInfo(`👤 ${detectionData.title || `${newCount} new person detected (${activeCount} total)`}`, 3000)
    }

    // Clear detection after 10 seconds
    setTimeout(() => {
      setCurrentDetection(prev => 
        prev?.id === newDetection.id ? null : prev
      )
    }, 10000)
  }, [showError, showWarning, showInfo])

  const clearDetection = useCallback(() => {
    setCurrentDetection(null)
  }, [])

  const setDetectionStatus = useCallback((status) => {
    setIsDetecting(status)
  }, [])

  const value = {
    currentDetection,
    detectionHistory,
    isDetecting,
    detectionCount,
    updateDetection,
    clearDetection,
    setDetectionStatus
  }

  return (
    <DetectionContext.Provider value={value}>
      {children}
    </DetectionContext.Provider>
  )
}
