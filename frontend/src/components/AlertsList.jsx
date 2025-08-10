import { useState } from 'react'
import { format } from 'date-fns'
import clsx from 'clsx'

function AlertItem({ item }) {
  const [open, setOpen] = useState(false)
  const tone = item.severity || 'info'
  
  const colors = {
    critical: 'border-red-500/30 bg-red-500/5 hover:bg-red-500/10',
    high: 'border-amber-500/30 bg-amber-500/5 hover:bg-amber-500/10',
    medium: 'border-sky-500/30 bg-sky-500/5 hover:bg-sky-500/10',
    low: 'border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10',
    info: 'border-sky-500/30 bg-sky-500/5 hover:bg-sky-500/10',
  }
  
  const severityIcons = {
    critical: '🚨',
    high: '⚠️',
    medium: '🔶',
    low: '🟢',
    info: 'ℹ️',
  }
  
  return (
    <div className={clsx(
      'border rounded-xl p-4 transition-all duration-200 backdrop-blur-sm', 
      colors[tone] || 'border-zinc-700/50 bg-zinc-800/20 hover:bg-zinc-800/40'
    )}> 
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start space-x-3 flex-1">
          <span className="text-lg mt-0.5">{severityIcons[tone] || '📡'}</span>
          <div className="flex-1">
            <div className="font-semibold text-zinc-200 text-sm leading-tight">
              {item.title || item.reason || 'Security Alert'}
            </div>
            <div className="text-xs text-zinc-400 mt-2 space-y-1">
              <div className="flex items-center space-x-4">
                <span>🕐 {format(new Date(item.timestamp || item.time || Date.now()), 'MMM dd, HH:mm')}</span>
                {item.severity && (
                  <span className="px-2 py-0.5 rounded-full bg-zinc-700/50 text-xs font-medium uppercase tracking-wider">
                    {item.severity}
                  </span>
                )}
              </div>
              {item.location && (
                <div className="flex items-center space-x-1">
                  <span>📍</span>
                  <span>{item.location}</span>
                </div>
              )}
              {item.lat && item.lng && (
                <div className="flex items-center space-x-1">
                  <span>🌐</span>
                  <span>{item.lat.toFixed?.(4)}, {item.lng.toFixed?.(4)}</span>
                </div>
              )}
            </div>
          </div>
        </div>
        <button 
          onClick={() => setOpen((v) => !v)} 
          className="text-xs border border-zinc-600/50 px-3 py-1.5 rounded-lg bg-zinc-800/50 hover:bg-zinc-700/50 transition-colors flex items-center space-x-1"
        >
          <span>{open ? 'Hide' : 'More'}</span>
          <span className="transform transition-transform duration-200" style={{transform: open ? 'rotate(180deg)' : 'rotate(0deg)'}}>
            ⌄
          </span>
        </button>
      </div>
      
      {open && item.details && (
        <div className="mt-4 pt-4 border-t border-zinc-700/30">
          <div className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
            {item.details}
          </div>
        </div>
      )}
      
      {open && item.detections && (
        <div className="mt-4 pt-4 border-t border-zinc-700/30">
          <div className="text-sm text-zinc-400 mb-3 font-medium">Detection Results</div>
          <pre className="text-xs bg-zinc-950/60 border border-zinc-700/30 p-4 rounded-lg overflow-auto max-h-40 text-zinc-300">
            {JSON.stringify(item.detections, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default function AlertsList({ items = [] }) {
  if (!items.length) {
    return (
      <div className="text-center py-12">
        <div className="text-zinc-400 text-4xl mb-3">🔍</div>
        <div className="text-zinc-400 text-sm">No alerts detected</div>
        <div className="text-zinc-500 text-xs mt-1">System monitoring active</div>
      </div>
    )
  }
  
  return (
    <div className="space-y-4">
      {items.map((a, index) => (
        <AlertItem key={a.id || a.timestamp || index} item={a} />
      ))}
    </div>
  )
}