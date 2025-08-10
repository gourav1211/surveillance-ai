import axios from 'axios'

// Base Axios instance; update baseURL if needed.
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 15000,
})

export const getStreamInfo = () => api.get('/stream')
export const getStats = () => api.get('/analytics/summary')
export const getAlerts = (params) => api.get('/alerts', { params })

// Example SSE endpoint for live alerts
export function subscribeAlerts(onMessage) {
  const url = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api') + '/alerts/stream'
  const es = new EventSource(url)
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      onMessage?.(data)
    } catch (err) {
      console.error('SSE parse error', err)
    }
  }
  return () => es.close()
}
