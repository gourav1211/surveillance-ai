import { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'
import { useToast } from '../contexts/ToastContext'

export default function VideoPlayer({ src, className = '' }) {
  const videoRef = useRef(null)
  const [isLoading, setIsLoading] = useState(!!src)
  const [hasError, setHasError] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const hlsRef = useRef(null)
  const { showError, showWarning, showSuccess } = useToast()

  const retryConnection = () => {
    if (retryCount < 3) {
      setRetryCount(prev => prev + 1)
      setHasError(false)
      setIsLoading(true)
      setConnectionStatus('connecting')
      showWarning(`Attempting to reconnect to video stream (${retryCount + 1}/3)...`, 3000)
      
      // Force re-render by updating a dependency
      setTimeout(() => {
        const video = videoRef.current
        if (video && src) {
          // Try to reconnect
          initializeVideo()
        }
      }, 2000)
    } else {
      showError('Video stream connection failed after 3 attempts. Please check the stream source.', 8000)
    }
  }

  const initializeVideo = () => {
    const video = videoRef.current
    if (!video || !src) {
      setConnectionStatus('disconnected')
      return
    }

    setIsLoading(true)
    setHasError(false)
    setConnectionStatus('connecting')

    // Clean up existing HLS instance
    if (hlsRef.current) {
      hlsRef.current.destroy()
      hlsRef.current = null
    }

    if (Hls.isSupported()) {
      const hls = new Hls({ 
        lowLatencyMode: true,
        liveSyncDurationCount: 3,
        liveMaxLatencyDurationCount: 5,
        enableWorker: true,
        debug: false
      })
      
      hlsRef.current = hls
      
      hls.loadSource(src)
      hls.attachMedia(video)
      
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setIsLoading(false)
        setRetryCount(0)
        setConnectionStatus('connected')
        if (retryCount > 0) {
          showSuccess('Video stream reconnected successfully!', 3000)
        }
        video.play().catch(err => {
          console.warn('Auto-play failed:', err)
        })
      })
      
      hls.on(Hls.Events.ERROR, (event, data) => {
        console.warn('HLS error:', data)
        if (data.fatal) {
          setHasError(true)
          setConnectionStatus('error')
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.log('Network error, trying to recover...')
              showWarning('Network error detected. Attempting to recover...', 4000)
              hls.startLoad()
              break
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.log('Media error, trying to recover...')
              showWarning('Media playback error. Attempting to recover...', 4000)
              hls.recoverMediaError()
              break
            default:
              console.log('Fatal error, destroying HLS...')
              showError('Fatal stream error. Please try refreshing the page.', 6000)
              hls.destroy()
              break
          }
        }
      })
      
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = src
      video.onloadeddata = () => {
        setIsLoading(false)
        setRetryCount(0)
        setConnectionStatus('connected')
        if (retryCount > 0) {
          showSuccess('Video stream reconnected successfully!', 3000)
        }
        video.play().catch(err => {
          console.warn('Auto-play failed:', err)
        })
      }
      video.onerror = (err) => {
        console.error('Video error:', err)
        setHasError(true)
        setConnectionStatus('error')
        showError('Video playback error. Stream may be unavailable.', 5000)
      }
    } else {
      setHasError(true)
      setConnectionStatus('unsupported')
      showError('HLS not supported in this browser. Please use a modern browser.', 8000)
      console.error('HLS not supported in this browser')
    }
  }

  useEffect(() => {
    initializeVideo()

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy()
        hlsRef.current = null
      }
    }
  }, [src])

  return (
    <div className={`relative bg-black rounded-xl overflow-hidden border border-zinc-800/50 shadow-2xl ${className}`}>
      {/* Video Element */}
      <video 
        ref={videoRef} 
        controls 
        autoPlay 
        muted 
        className="w-full h-full aspect-video bg-zinc-900" 
      />
      
      {/* LIVE Indicator */}
      {connectionStatus === 'connected' && (
        <div className="absolute top-4 left-4 flex items-center space-x-2 bg-red-600/90 backdrop-blur-sm px-3 py-1.5 rounded-lg">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
          <span className="text-white text-sm font-semibold">LIVE</span>
        </div>
      )}

      {/* Connection Status Indicator */}
      {connectionStatus === 'connecting' && (
        <div className="absolute top-4 left-4 flex items-center space-x-2 bg-yellow-600/90 backdrop-blur-sm px-3 py-1.5 rounded-lg">
          <div className="w-2 h-2 bg-white rounded-full animate-spin"></div>
          <span className="text-white text-sm font-semibold">CONNECTING</span>
        </div>
      )}

      {/* Error Status Indicator */}
      {connectionStatus === 'error' && !isLoading && (
        <div className="absolute top-4 left-4 flex items-center space-x-2 bg-red-800/90 backdrop-blur-sm px-3 py-1.5 rounded-lg">
          <div className="w-2 h-2 bg-white rounded-full"></div>
          <span className="text-white text-sm font-semibold">OFFLINE</span>
        </div>
      )}

      {/* Stream Info */}
      {connectionStatus === 'connected' && (
        <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-lg">
          <span className="text-white text-xs">HD • 1080p</span>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="absolute inset-0 bg-zinc-900/80 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full mx-auto mb-3"></div>
            <div className="text-zinc-300 text-sm">Connecting to stream...</div>
          </div>
        </div>
      )}

      {/* Error State */}
      {hasError && !isLoading && (
        <div className="absolute inset-0 bg-zinc-900/80 flex items-center justify-center">
          <div className="text-center">
            <div className="text-red-400 text-4xl mb-3">📹</div>
            <div className="text-zinc-300 text-sm">Stream unavailable</div>
            <div className="text-zinc-500 text-xs mt-1">Check connection or try again</div>
            {retryCount < 3 && (
              <button 
                onClick={retryConnection}
                className="mt-3 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
              >
                Retry Connection ({retryCount}/3)
              </button>
            )}
          </div>
        </div>
      )}

      {/* No Stream State */}
      {!src && (
        <div className="absolute inset-0 bg-zinc-900/80 flex items-center justify-center">
          <div className="text-center">
            <div className="text-zinc-400 text-4xl mb-3">📡</div>
            <div className="text-zinc-300 text-sm">No stream configured</div>
            <div className="text-zinc-500 text-xs mt-1">Waiting for video feed...</div>
          </div>
        </div>
      )}
    </div>
  )
}
