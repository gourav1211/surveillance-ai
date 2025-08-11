import { createContext, useContext, useState, useCallback } from 'react'
import Toast from '../components/Toast'

const ToastContext = createContext()

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const showToast = useCallback((message, type = 'error', duration = 5000) => {
    const id = Date.now() + Math.random()
    const newToast = { id, message, type, duration }
    
    setToasts(prev => [...prev, newToast])

    // Auto remove after duration
    if (duration > 0) {
      setTimeout(() => {
        setToasts(prev => prev.filter(toast => toast.id !== id))
      }, duration + 300) // Add extra time for fade out
    }

    return id
  }, [])

  const hideToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }, [])

  const showError = useCallback((message, duration) => showToast(message, 'error', duration), [showToast])
  const showWarning = useCallback((message, duration) => showToast(message, 'warning', duration), [showToast])
  const showInfo = useCallback((message, duration) => showToast(message, 'info', duration), [showToast])
  const showSuccess = useCallback((message, duration) => showToast(message, 'success', duration), [showToast])

  return (
    <ToastContext.Provider value={{ showToast, showError, showWarning, showInfo, showSuccess, hideToast }}>
      {children}
      {toasts.map(toast => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          isVisible={true}
          duration={toast.duration}
          onClose={() => hideToast(toast.id)}
        />
      ))}
    </ToastContext.Provider>
  )
}
