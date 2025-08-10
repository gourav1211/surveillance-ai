import { useEffect, useState } from 'react'
import VideoPlayer from '../components/VideoPlayer'
import StatCard from '../components/StatCard'
import AlertsChart from '../components/AlertsChart'
import AlertsList from '../components/AlertsList'
import { getStreamInfo, getStats, getAlerts, subscribeAlerts } from '../lib/api'

export default function Dashboard() {
  const [streamUrl, setStreamUrl] = useState('')
  const [stats, setStats] = useState({ total: 0, critical: 0, high: 0, blackout: 0 })
  const [alerts, setAlerts] = useState([])
  const [trend, setTrend] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let unsub = () => {}
    ;(async () => {
      try {
        const [sInfo, s, a] = await Promise.all([
          getStreamInfo().catch(() => ({ data: { url: '' } })),
          getStats().catch(() => ({ data: { total: 0, critical: 0, high: 0, blackout: 0, trend: [] } })),
          getAlerts({ limit: 20 }).catch(() => ({ data: [] })),
        ])
        setStreamUrl(sInfo?.data?.url || sInfo?.data?.hls || '')
        setStats({
          total: s?.data?.total ?? 42,
          critical: s?.data?.critical ?? s?.data?.attack ?? 3,
          high: s?.data?.high ?? s?.data?.danger ?? 8,
          blackout: s?.data?.blackout ?? 1,
        })
        setTrend(s?.data?.trend || [])
        
        // Sample alerts if no real data
        const sampleAlerts = a?.data?.length > 0 ? a.data : [
          {
            id: 1,
            timestamp: Date.now() - 5 * 60 * 1000,
            title: "Motion Detected - Restricted Area",
            reason: "Unauthorized personnel detected in secure zone",
            severity: "critical",
            location: "Warehouse Section A",
            lat: 40.7128,
            lng: -74.0060,
            details: "Multiple individuals detected entering restricted warehouse area at 02:45 AM. Security protocols activated.",
            detections: {
              objects: ["person", "person"],
              confidence: 0.94,
              zone: "restricted_area_1"
            }
          },
          {
            id: 2,
            timestamp: Date.now() - 15 * 60 * 1000,
            title: "Vehicle Speeding Alert",
            reason: "Vehicle exceeding speed limit",
            severity: "high",
            location: "Main Gate Access Road",
            lat: 40.7589,
            lng: -73.9851,
            details: "Vehicle traveling at 55 mph in 25 mph zone. License plate captured.",
            detections: {
              vehicle_type: "sedan",
              speed: 55,
              license_plate: "ABC-1234"
            }
          },
          {
            id: 3,
            timestamp: Date.now() - 30 * 60 * 1000,
            title: "Perimeter Breach",
            reason: "Fence line security compromised",
            severity: "medium",
            location: "East Perimeter - Section 7",
            lat: 40.7282,
            lng: -74.0776,
            details: "Possible fence damage detected. Requires inspection."
          }
        ]
        setAlerts(sampleAlerts)
      } finally {
        setLoading(false)
      }
      unsub = subscribeAlerts((msg) => {
        setAlerts((prev) => [msg, ...prev].slice(0, 50))
        setStats((p) => ({ ...p, total: (p.total || 0) + 1 }))
      })
    })()
    return () => unsub()
  }, [])

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
            <VideoPlayer src={streamUrl} />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Total Alerts" value={stats.total} tone="accent" />
              <StatCard label="Critical" value={stats.critical} tone="danger" />
              <StatCard label="High" value={stats.high} tone="warning" />
              <StatCard label="Blackouts" value={stats.blackout} tone="info" />
            </div>
            <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-xl p-6 backdrop-blur-sm">
              <div className="text-lg font-semibold text-zinc-200 mb-4">Alert Trends</div>
              <AlertsChart data={trend} />
            </div>
          </div>
          <div className="lg:col-span-1">
            <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-xl p-6 backdrop-blur-sm sticky top-8 max-h-[calc(100vh-8rem)] overflow-hidden flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <div className="text-lg font-semibold text-zinc-200">Live Updates</div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-red-400 font-medium">LIVE</span>
                </div>
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