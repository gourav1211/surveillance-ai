import { useDetection } from '../contexts/DetectionContext'
import { format } from 'date-fns'

export default function DetectionOverlay({ videoRef }) {
  const { currentDetection, isDetecting } = useDetection()

  if (!currentDetection || !videoRef?.current) {
    return null
  }

  const video = videoRef.current
  const videoRect = video.getBoundingClientRect()
  const videoWidth = video.videoWidth || videoRect.width || 640
  const videoHeight = video.videoHeight || videoRect.height || 480

  // Don't render bounding boxes if we don't have proper video dimensions
  const hasValidDimensions = video.videoWidth > 0 && video.videoHeight > 0

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-500/20'
      case 'high': return 'border-orange-500 bg-orange-500/20'
      case 'medium': return 'border-yellow-500 bg-yellow-500/20'
      default: return 'border-blue-500 bg-blue-500/20'
    }
  }

  const getSeverityTextColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-400'
      case 'high': return 'text-orange-400'
      case 'medium': return 'text-yellow-400'
      default: return 'text-blue-400'
    }
  }

  const getDetectionIcon = (detection) => {
    // Check for weapon detection first
    if (detection.objectTypes?.includes('weapon')) return '⚔️'
    
    const personCount = detection.personCount || 0
    if (personCount > 2) return '🚨'
    if (personCount > 1) return '⚠️'
    return '👤'
  }

  const getDetectionText = (detection) => {
    // Check for weapon detection first
    if (detection.objectTypes?.includes('weapon')) {
      return 'Weapon Detected'
    }
    
    const personCount = detection.personCount || 0
    if (personCount > 0) {
      return `${personCount} Person${personCount > 1 ? 's' : ''} Detected`
    }
    
    return 'Object Detected'
  }

  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Detection Alert Banner */}
      <div className={`absolute top-0 left-0 right-0 bg-gradient-to-r ${getSeverityColor(currentDetection.severity)} border-b-2 border-current p-3 backdrop-blur-sm z-10`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`text-2xl ${currentDetection.personCount > 1 || currentDetection.objectTypes?.includes('weapon') ? 'animate-pulse' : ''}`}>
              {getDetectionIcon(currentDetection)}
            </div>
            <div>
              <div className={`font-bold text-lg ${getSeverityTextColor(currentDetection.severity)}`}>
                {getDetectionText(currentDetection)}
              </div>
              <div className="text-sm text-white/80">
                Detected at {format(currentDetection.timestamp, 'HH:mm:ss')}
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full animate-pulse ${getSeverityTextColor(currentDetection.severity).replace('text-', 'bg-')}`}></div>
            <span className={`text-sm font-medium ${getSeverityTextColor(currentDetection.severity)}`}>
              {currentDetection.severity.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Bounding Boxes */}
      {currentDetection.boxes && currentDetection.boxes.length > 0 && hasValidDimensions && (
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 5 }}>
          {currentDetection.boxes.map((box, index) => {
            const [x1, y1, x2, y2, confidence] = box
            const width = ((x2 - x1) / videoWidth) * 100
            const height = ((y2 - y1) / videoHeight) * 100
            const left = (x1 / videoWidth) * 100
            const top = (y1 / videoHeight) * 100

            return (
              <g key={index}>
                {/* Bounding Box */}
                <rect
                  x={`${left}%`}
                  y={`${top}%`}
                  width={`${width}%`}
                  height={`${height}%`}
                  fill="none"
                  stroke={currentDetection.severity === 'critical' ? '#ef4444' : 
                         currentDetection.severity === 'high' ? '#f97316' : 
                         currentDetection.severity === 'medium' ? '#eab308' : '#3b82f6'}
                  strokeWidth="2"
                  strokeDasharray="5,5"
                  className="animate-pulse"
                />
                
                {/* Corner Indicators */}
                <rect
                  x={`${left}%`}
                  y={`${top}%`}
                  width="8"
                  height="8"
                  fill={currentDetection.severity === 'critical' ? '#ef4444' : 
                       currentDetection.severity === 'high' ? '#f97316' : 
                       currentDetection.severity === 'medium' ? '#eab308' : '#3b82f6'}
                />
                <rect
                  x={`${left + width}%`}
                  y={`${top}%`}
                  width="8"
                  height="8"
                  fill={currentDetection.severity === 'critical' ? '#ef4444' : 
                       currentDetection.severity === 'high' ? '#f97316' : 
                       currentDetection.severity === 'medium' ? '#eab308' : '#3b82f6'}
                  transform="translate(-8, 0)"
                />
                <rect
                  x={`${left}%`}
                  y={`${top + height}%`}
                  width="8"
                  height="8"
                  fill={currentDetection.severity === 'critical' ? '#ef4444' : 
                       currentDetection.severity === 'high' ? '#f97316' : 
                       currentDetection.severity === 'medium' ? '#eab308' : '#3b82f6'}
                  transform="translate(0, -8)"
                />
                <rect
                  x={`${left + width}%`}
                  y={`${top + height}%`}
                  width="8"
                  height="8"
                  fill={currentDetection.severity === 'critical' ? '#ef4444' : 
                       currentDetection.severity === 'high' ? '#f97316' : 
                       currentDetection.severity === 'medium' ? '#eab308' : '#3b82f6'}
                  transform="translate(-8, -8)"
                />
              </g>
            )
          })}
        </svg>
      )}

      {/* Detection Status Indicator */}
      {isDetecting && (
        <div className="absolute bottom-4 right-4 bg-green-600/90 backdrop-blur-sm px-3 py-1.5 rounded-lg flex items-center space-x-2">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
          <span className="text-white text-sm font-semibold">DETECTING</span>
        </div>
      )}
    </div>
  )
}
