import { useEffect, useState } from 'react'
import VideoPlayer from '../components/VideoPlayer'
import StatCard from '../components/StatCard'
import AlertsChart from '../components/AlertsChart'
import AlertsList from '../components/AlertsList'
import { getStreamInfo, getStats, getAlerts, getDetectionStatus, subscribeAlerts } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { useDetection } from '../contexts/DetectionContext'
import DetectionIndicator from '../components/DetectionIndicator'

// Helper function to create hourly trend data from alerts
function createHourlyTrend(alerts, hours = 6) {
  const now = new Date()
  const trendData = []
  
  for (let i = hours - 1; i >= 0; i--) {
    const hourStart = new Date(now)
    hourStart.setHours(now.getHours() - i, 0, 0, 0)
    
    const hourEnd = new Date(hourStart)
    hourEnd.setHours(hourStart.getHours() + 1)
    
    // Count alerts in this hour
    const alertsInHour = alerts.filter(alert => {
      const alertTime = new Date(alert.timestamp)
      return alertTime >= hourStart && alertTime < hourEnd
    })
    
    trendData.push({
      time: hourStart.getTime(),
      alerts: alertsInHour.length,
      count: alertsInHour.length // Alternative field name that AlertsChart supports
    })
  }
  
  return trendData
}

export default function Dashboard() {
  const [streamUrl, setStreamUrl] = useState('')
  const [stats, setStats] = useState({ total: 0, critical: 0, high: 0, blackout: 0 })
  const [alerts, setAlerts] = useState([])
  const [trend, setTrend] = useState([])
  const [loading, setLoading] = useState(true)
  const [detectionStatus, setDetectionStatus] = useState({ is_running: false })
  const { showError, showWarning, showInfo, showSuccess } = useToast()
  const { updateDetection, setDetectionStatus: setDetectionContextStatus, detectionCount } = useDetection()

  useEffect(() => {
    let unsub = () => {}
    ;(async () => {
      try {
        // Handle stream info with error messaging
        let streamData = null
        try {
          const sInfo = await getStreamInfo()
          streamData = sInfo?.data || {}
        } catch (error) {
          console.warn('Stream endpoint error:', error)
          showWarning('Video stream is currently unavailable. The application will continue to work with other features.', 6000)
          streamData = { url: '', status: 'unavailable' }
        }

        // Handle stats
        let statsData = null
        try {
          const s = await getStats()
          statsData = s?.data || {}
        } catch (error) {
          console.warn('Stats endpoint error:', error)
          showError('Unable to load analytics data.', 4000)
          statsData = { total: 0, critical: 0, high: 0, blackout: 0, trend: [] }
        }

        // Handle alerts
        let alertsData = []
        try {
          const a = await getAlerts({ limit: 20 })
          alertsData = a?.data || []
        } catch (error) {
          console.warn('Alerts endpoint error:', error)
          showError('Unable to load alerts data.', 4000)
          alertsData = []
        }

        // Handle detection status
        let detectionData = { is_running: false }
        try {
          const d = await getDetectionStatus()
          detectionData = d?.data || { is_running: false }
          setDetectionStatus(detectionData)
          setDetectionContextStatus(detectionData.is_running)
          
          if (detectionData.is_running) {
            showSuccess('Person detection is active and monitoring the stream!', 3000)
          } else {
            showWarning('Person detection is not running. Alerts may not be real-time.', 5000)
          }
        } catch (error) {
          console.warn('Detection status endpoint error:', error)
          showWarning('Unable to check detection status.', 4000)
        }
        
        // Process stream data
        if (streamData.status === 'active' && (streamData.url || streamData.hls)) {
          setStreamUrl(streamData.url || streamData.hls)
          showInfo('Video stream connected successfully!', 3000)
        } else {
          setStreamUrl('') // Clear stream URL if not active
          if (streamData.error) {
            console.warn('Stream unavailable:', streamData.error)
          }
        }

        // Process stats data - but don't use the dummy trend data
        setStats({
          total: statsData.total || 0,
          critical: statsData.critical || 0,
          high: statsData.high || 0,
          blackout: statsData.blackout || 0,
        })
        // Don't use statsData.trend - we'll create our own from real alerts
        
        // Set real alerts data and create trend from it
        setAlerts(alertsData)
        setTrend(createHourlyTrend(alertsData, 6))
        
      } catch (error) {
        console.error('Critical error loading dashboard:', error)
        showError('Failed to load dashboard data. Please refresh the page.', 8000)
      } finally {
        setLoading(false)
      }

              // Setup real-time alerts subscription with error handling
        try {
          unsub = subscribeAlerts(
            (msg) => {
              // Use functional update to get the current alerts
              setAlerts((prevAlerts) => {
                const updatedAlerts = [msg, ...prevAlerts].slice(0, 50)
                
                // Update trend data with the new alerts
                setTrend(createHourlyTrend(updatedAlerts, 6))
                
                return updatedAlerts
              })
              
              // Update detection context with real-time data
              updateDetection(msg)
              
              // Update stats
              setStats((p) => ({ 
                ...p, 
                total: (p.total || 0) + 1,
                critical: p.critical + (msg.severity === 'critical' ? 1 : 0),
                high: p.high + (msg.severity === 'high' ? 1 : 0)
              }))
              
              // Show notification for new detections
              if (msg.severity === 'critical') {
                showError(`🚨 ${msg.title}`, 5000)
              } else if (msg.severity === 'high') {
                showWarning(`⚠️ ${msg.title}`, 4000)
              } else {
                showInfo(`🔶 ${msg.title}`, 3000)
              }
            },
            (errorMsg) => {
              console.warn('SSE Error:', errorMsg)
              showWarning(errorMsg + ' Data will refresh periodically instead.', 5000)
            }
          )
        } catch (error) {
          console.warn('Failed to setup real-time alerts:', error)
          showWarning('Real-time alerts are not available. Data will refresh periodically.', 5000)
        }
    })()
    return () => unsub()
  }, [showError, showInfo, showSuccess, showWarning, updateDetection, setDetectionContextStatus])

  const header = (
    <div className="flex items-center justify-between py-6 border-b border-zinc-800/50">
      <div className="flex items-center space-x-3">
        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
        <div className="text-2xl font-bold tracking-tight">
          <span className="text-blue-400">SURVEILLANCE</span>
          <span className="text-zinc-300 ml-2">AI</span>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${detectionStatus.is_running ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
          <span className="text-sm text-zinc-400">
            {detectionStatus.is_running ? 'Detection Active' : 'Detection Inactive'}
          </span>
        </div>
        <div className="text-sm text-zinc-400">
          <span className="text-green-400">●</span> System Online
        </div>
        <div className="text-sm text-zinc-500">{new Date().toLocaleString()}</div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 text-white">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        {header}
        <div className="grid lg:grid-cols-3 gap-8 py-8">
          <div className="lg:col-span-2 space-y-6">
            <VideoPlayer 
              src={streamUrl}
              onStreamConnectedChange={(connected) => setDetectionContextStatus(connected && detectionStatus.is_running)}
            />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Total Alerts" value={stats.total} tone="accent" />
              <StatCard label="Critical" value={stats.critical} tone="danger" />
              <StatCard label="High" value={stats.high} tone="warning" />
              <StatCard label="Detections" value={detectionCount} tone="success" />
            </div>
            <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-xl p-6 backdrop-blur-sm">
              <div className="text-lg font-semibold text-zinc-200 mb-4">Alert Trends (Last 6 Hours)</div>
              <AlertsChart data={trend} />
            </div>
          </div>
          <div className="lg:col-span-1">
            <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-xl p-6 backdrop-blur-sm sticky top-8 max-h-[calc(100vh-8rem)] overflow-hidden flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <div className="text-lg font-semibold text-zinc-200">Live Updates</div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full animate-pulse ${detectionStatus.is_running ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className={`text-xs font-medium ${detectionStatus.is_running ? 'text-green-400' : 'text-red-400'}`}>
                    {detectionStatus.is_running ? 'DETECTING' : 'OFFLINE'}
                  </span>
                </div>
              </div>
              
              <div className="mb-4">
                <DetectionIndicator />
              </div>
              
              <div className="flex-1 overflow-auto">
                <AlertsList items={alerts} />
              </div>
            </div>
          </div>
        </div>
        {loading && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm grid place-items-center">
            <div className="bg-zinc-900/90 border border-zinc-700 rounded-xl p-8 text-center">
              <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full mx-auto mb-4"></div>
              <div className="text-zinc-300">Loading surveillance data...</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}