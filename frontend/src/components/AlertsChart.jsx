import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart } from 'recharts'
import { format } from 'date-fns'

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    let formattedTime;
    try {
      const date = new Date(label);
      if (isNaN(date.getTime())) {
        formattedTime = 'Invalid time';
      } else {
        // Show hour range for hourly data
        const endHour = new Date(date);
        endHour.setHours(date.getHours() + 1);
        formattedTime = `${format(date, 'HH:mm')} - ${format(endHour, 'HH:mm')}`;
      }
    } catch (error) {
      formattedTime = 'Invalid time';
    }
    
    return (
      <div className="bg-zinc-900/90 border border-zinc-700/50 backdrop-blur-sm rounded-lg p-3 shadow-xl">
        <p className="text-zinc-300 text-sm font-medium">
          {formattedTime}
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
  // Process real data only, no fallback dummy data
  const chartData = data.length > 0 ? data.map(d => {
    let timeValue;
    
    // Handle different time formats
    if (typeof d.time === 'string') {
      // If it's a time string like "12:00", convert to timestamp
      if (d.time.includes(':')) {
        const [hours, minutes] = d.time.split(':').map(Number);
        const today = new Date();
        today.setHours(hours, minutes, 0, 0);
        timeValue = today.getTime();
      } else {
        // Try to parse as ISO string or timestamp
        timeValue = new Date(d.time).getTime();
      }
    } else if (typeof d.time === 'number') {
      timeValue = d.time;
    } else if (d.timestamp) {
      timeValue = d.timestamp;
    } else {
      // Fallback to current time
      timeValue = Date.now();
    }
    
    // Validate the time value
    if (isNaN(timeValue)) {
      timeValue = Date.now();
    }
    
    return {
      time: timeValue,
      alerts: d.count || d.alerts || 0,
    };
  }) : [];
  
  return (
    <div className="h-72 w-full">
      {chartData.length === 0 ? (
        <div className="flex items-center justify-center h-full text-zinc-500">
          <div className="text-center">
            <div className="text-sm">No alert data available</div>
            <div className="text-xs mt-1">Data will appear when detections occur</div>
          </div>
        </div>
      ) : (
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
              tickFormatter={(t) => {
                try {
                  const date = new Date(t);
                  if (isNaN(date.getTime())) {
                    return '--:--';
                  }
                  // For hourly data, show hour format
                  return format(date, 'HH:mm');
                } catch (error) {
                  console.warn('Invalid time value for chart:', t);
                  return '--:--';
                }
              }} 
              stroke="#9ca3af" 
              tick={{ fontSize: 12, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
              interval={0}
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
      )}
    </div>
  )
}
