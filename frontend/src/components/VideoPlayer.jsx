import { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'

export default function VideoPlayer({ src, className = '' }) {
  const videoRef = useRef(null)
  const [isLoading, setIsLoading] = useState(!!src)
  const [hasError, setHasError] = useState(false)

  useEffect(() => {
    const video = videoRef.current
    if (!video || !src) return

    setIsLoading(true)
    setHasError(false)

    let hls
    if (Hls.isSupported()) {
      hls = new Hls({ lowLatencyMode: true })
      hls.loadSource(src)
      hls.attachMedia(video)
      hls.on(Hls.Events.MANIFEST_LOADED, () => setIsLoading(false))
      hls.on(Hls.Events.ERROR, () => setHasError(true))
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = src
      video.onloadeddata = () => setIsLoading(false)
      video.onerror = () => setHasError(true)
      video.play().catch(() => setHasError(true))
    }
    return () => {
      if (hls) hls.destroy()
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
      <div className="absolute top-4 left-4 flex items-center space-x-2 bg-red-600/90 backdrop-blur-sm px-3 py-1.5 rounded-lg">
        <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
        <span className="text-white text-sm font-semibold">LIVE</span>
      </div>

      {/* Stream Info */}
      <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-lg">
        <span className="text-white text-xs">HD • 1080p</span>
      </div>

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
