import { useDetection } from '../contexts/DetectionContext'
import { format } from 'date-fns'

export default function DetectionIndicator() {
  const { currentDetection, detectionCount, isDetecting } = useDetection()

  if (!isDetecting) {
    return (
      <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
        <div className="flex items-center space-x-2 text-sm">
          <span className="text-red-400">🔴</span>
          <span className="text-red-300">Detection offline</span>
        </div>
        <div className="text-xs text-red-400/70 mt-1">
          No active monitoring
        </div>
      </div>
    )
  }

  if (!currentDetection) {
    return (
      <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
        <div className="flex items-center space-x-2 text-sm">
          <span className="text-green-400">🟢</span>
          <span className="text-green-300">Monitoring active</span>
        </div>
        <div className="text-xs text-green-400/70 mt-1">
          {detectionCount} total detections
        </div>
      </div>
    )
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-500/10 border-red-500/20 text-red-300'
      case 'high': return 'bg-orange-500/10 border-orange-500/20 text-orange-300'
      case 'medium': return 'bg-yellow-500/10 border-yellow-500/20 text-yellow-300'
      default: return 'bg-blue-500/10 border-blue-500/20 text-blue-300'
    }
  }

  const getSeverityIcon = (severity, objectTypes = ['person']) => {
    // Prioritize weapon detection
    if (objectTypes.includes('weapon')) return '⚔️'
    
    switch (severity) {
      case 'critical': return '🚨'
      case 'high': return '⚠️'
      case 'medium': return '🔶'
      default: return '👤'
    }
  }

  const getObjectTypeText = (objectTypes = ['person'], personCount = 0) => {
    if (objectTypes.includes('weapon')) {
      return '⚔️ Weapon Detected'
    }
    if (objectTypes.includes('vehicle')) {
      return '🚗 Vehicle Detected'
    }
    if (personCount > 0) {
      return `👤 ${personCount} Person${personCount > 1 ? 's' : ''} Detected`
    }
    return 'Object Detected'
  }

  return (
    <div className={`p-3 border rounded-lg ${getSeverityColor(currentDetection.severity)}`}>
      <div className="flex items-center space-x-2 text-sm">
        <span className={`text-lg ${currentDetection.personCount > 1 || currentDetection.objectTypes?.includes('weapon') ? 'animate-pulse' : ''}`}>
          {getSeverityIcon(currentDetection.severity, currentDetection.objectTypes)}
        </span>
        <span className="font-medium">
          {getObjectTypeText(currentDetection.objectTypes, currentDetection.personCount)}
        </span>
      </div>
      <div className="text-xs opacity-70 mt-1 space-y-1">
        <div>Time: {format(currentDetection.timestamp, 'HH:mm:ss')}</div>
        <div>Severity: {currentDetection.severity?.toUpperCase()}</div>
        <div>Total: {detectionCount} detections</div>
      </div>
    </div>
  )
}
