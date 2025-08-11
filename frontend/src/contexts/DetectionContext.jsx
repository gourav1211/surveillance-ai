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

    const newDetection = {
      id: Date.now(),
      timestamp: Date.now(),
      personCount: detectionData.person_count || 0,
      confidence: detectionData.detections?.confidence || 0,
      boxes: detectionData.detections?.boxes || [],
      severity: detectionData.severity || 'medium',
      isActive: true
    }

    setCurrentDetection(newDetection)
    setDetectionCount(prev => prev + 1)
    
    // Add to history
    setDetectionHistory(prev => [newDetection, ...prev.slice(0, 49)]) // Keep last 50
    
    // Show appropriate notification
    if (newDetection.personCount > 2) {
      showError(`🚨 ${newDetection.personCount} persons detected!`, 5000)
    } else if (newDetection.personCount > 1) {
      showWarning(`⚠️ ${newDetection.personCount} persons detected`, 4000)
    } else {
      showInfo(`👤 Person detected`, 3000)
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
