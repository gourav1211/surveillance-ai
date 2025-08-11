import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import { ToastProvider } from './contexts/ToastContext'
import { DetectionProvider } from './contexts/DetectionContext'
import './index.css'

export default function App() {
  return (
    <ToastProvider>
      <DetectionProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/*" element={<Dashboard />} />
          </Routes>
        </BrowserRouter>
      </DetectionProvider>
    </ToastProvider>
  )
}
