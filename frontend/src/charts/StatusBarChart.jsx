import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { colorForStatus } from '../utils/chartColors'

function humanize(status) {
  return String(status || '')
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export default function StatusBarChart({ data, statusKey = 'status', valueKey = 'count', height = 220 }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-slate-400 py-12 text-center">No data available.</p>
  }
  const chartData = data.map((d) => ({ ...d, label: humanize(d[statusKey]) }))
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} interval={0} angle={-20} textAnchor="end" height={50} />
        <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} allowDecimals={false} />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }} />
        <Bar dataKey={valueKey} radius={[4, 4, 0, 0]} maxBarSize={40}>
          {chartData.map((d, i) => (
            <Cell key={i} fill={colorForStatus(d[statusKey])} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
