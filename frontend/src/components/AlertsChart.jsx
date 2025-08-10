import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart } from 'recharts'
import { format } from 'date-fns'

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-zinc-900/90 border border-zinc-700/50 backdrop-blur-sm rounded-lg p-3 shadow-xl">
        <p className="text-zinc-300 text-sm font-medium">
          {format(new Date(label), 'MMM dd, HH:mm')}
        </p>
        <p className="text-blue-400 text-sm">
          <span className="inline-block w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
          Alerts: {payload[0].value}
        </p>
      </div>
    );
  }
  return null;
}

export default function AlertsChart({ data = [] }) {
  // Generate sample data if none provided
  const chartData = data.length > 0 ? data.map(d => ({
    time: d.time || d.timestamp || d.t,
    alerts: d.count || d.alerts || 0,
  })) : [
    { time: Date.now() - 6 * 60 * 60 * 1000, alerts: 2 },
    { time: Date.now() - 5 * 60 * 60 * 1000, alerts: 5 },
    { time: Date.now() - 4 * 60 * 60 * 1000, alerts: 3 },
    { time: Date.now() - 3 * 60 * 60 * 1000, alerts: 8 },
    { time: Date.now() - 2 * 60 * 60 * 1000, alerts: 4 },
    { time: Date.now() - 1 * 60 * 60 * 1000, alerts: 6 },
    { time: Date.now(), alerts: 3 },
  ];
  
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ left: 10, right: 10, top: 10, bottom: 10 }}>
          <defs>
            <linearGradient id="alertGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#374151" strokeDasharray="3 3" vertical={false} />
          <XAxis 
            dataKey="time" 
            tickFormatter={(t) => format(new Date(t), 'HH:mm')} 
            stroke="#9ca3af" 
            tick={{ fontSize: 12, fill: '#9ca3af' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            stroke="#9ca3af" 
            tick={{ fontSize: 12, fill: '#9ca3af' }} 
            allowDecimals={false}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey="alerts" 
            stroke="#3b82f6" 
            strokeWidth={2}
            fill="url(#alertGradient)"
            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, fill: '#3b82f6', strokeWidth: 2, stroke: '#1e40af' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
