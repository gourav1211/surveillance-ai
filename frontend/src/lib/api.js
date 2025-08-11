import axios from 'axios'

// Base Axios instance; update baseURL if needed.
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 15000,
})

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      const customError = new Error('Unable to connect to the server. Please check if the backend is running.')
      customError.originalError = error
      customError.isNetworkError = true
      throw customError
    }
    
    if (error.response?.status === 503) {
      const customError = new Error('Service temporarily unavailable. The requested feature may be offline.')
      customError.originalError = error
      customError.isServiceError = true
      throw customError
    }
    
    if (error.response?.status >= 500) {
      const customError = new Error('Server error. Please try again later.')
      customError.originalError = error
      customError.isServerError = true
      throw customError
    }
    
    throw error
  }
)

export const getStreamInfo = () => api.get('/stream')
export const getStats = () => api.get('/analytics/summary')
export const getAlerts = (params) => api.get('/alerts', { params })
export const getDetectionStatus = () => api.get('/detection/status')

// Example SSE endpoint for live alerts
export function subscribeAlerts(onMessage, onError) {
  const url = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api') + '/alerts/stream'
  
  try {
    const es = new EventSource(url)
    
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        
        // Handle keepalive messages
        if (data.type === 'keepalive') {
          return // Don't process keepalive messages
        }
        
        // Process actual alert messages
        onMessage?.(data)
      } catch (err) {
        console.error('SSE parse error', err)
        onError?.('Failed to parse real-time alert data')
      }
    }
    
    es.onerror = (err) => {
      console.error('SSE connection error', err)
      onError?.('Lost connection to real-time alerts')
    }
    
    es.onopen = () => {
      console.log('SSE connection established')
    }
    
    return () => {
      console.log('Closing SSE connection')
      es.close()
    }
  } catch (error) {
    console.error('Failed to setup SSE connection:', error)
    onError?.('Unable to setup real-time alerts')
    return () => {}
  }
}
