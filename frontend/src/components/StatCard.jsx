export default function StatCard({ label, value, tone = 'info' }) {
  const toneMap = {
    danger: 'bg-red-500/5 text-red-300 border-red-500/20 shadow-red-500/10',
    warning: 'bg-amber-500/5 text-amber-300 border-amber-500/20 shadow-amber-500/10',
    info: 'bg-sky-500/5 text-sky-300 border-sky-500/20 shadow-sky-500/10',
    accent: 'bg-violet-500/5 text-violet-300 border-violet-500/20 shadow-violet-500/10',
    success: 'bg-green-500/5 text-green-300 border-green-500/20 shadow-green-500/10',
  }
  
  const iconMap = {
    danger: '⚠️',
    warning: '🔶',
    info: '📊', 
    accent: '📈',
    success: '👤',
  }
  
  return (
    <div className={`relative bg-zinc-900/40 border backdrop-blur-sm rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 ${toneMap[tone] || ''}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-medium text-zinc-400 uppercase tracking-wider">{label}</div>
        <span className="text-lg">{iconMap[tone]}</span>
      </div>
      <div className="text-4xl font-bold tracking-tight">{value}</div>
    </div>
  )
}
