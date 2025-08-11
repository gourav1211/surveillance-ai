import { useEffect, useState } from 'react'

export default function Toast({ message, type = 'error', isVisible, onClose, duration = 5000 }) {
  const [show, setShow] = useState(isVisible)

  useEffect(() => {
    setShow(isVisible)
    if (isVisible && duration > 0) {
      const timer = setTimeout(() => {
        setShow(false)
        setTimeout(onClose, 300) // Allow fade out animation
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [isVisible, duration, onClose])

  if (!show) return null

  const typeStyles = {
    error: 'bg-red-900/90 border-red-700 text-red-100',
    warning: 'bg-yellow-900/90 border-yellow-700 text-yellow-100',
    info: 'bg-blue-900/90 border-blue-700 text-blue-100',
    success: 'bg-green-900/90 border-green-700 text-green-100'
  }

  const icons = {
    error: '⚠️',
    warning: '⚠️',
    info: 'ℹ️',
    success: '✅'
  }

  return (
    <div className={`
      fixed top-4 right-4 z-50 min-w-80 max-w-md p-4 border rounded-lg backdrop-blur-sm shadow-xl
      transition-all duration-300 ease-in-out
      ${show ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'}
      ${typeStyles[type]}
    `}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 text-lg">
          {icons[type]}
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium">{message}</p>
        </div>
        <button
          onClick={() => {
            setShow(false)
            setTimeout(onClose, 300)
          }}
          className="flex-shrink-0 text-lg opacity-70 hover:opacity-100 transition-opacity"
        >
          ×
        </button>
      </div>
    </div>
  )
}
