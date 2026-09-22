import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { SEQUENTIAL_BLUE } from '../utils/chartColors'

export default function AgingChart({ buckets, height = 220 }) {
  if (!buckets || buckets.length === 0) {
    return <p className="text-sm text-slate-400 py-12 text-center">No outstanding invoices.</p>
  }
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={buckets} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} allowDecimals={false} />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
          formatter={(value, name) => [name === 'amount' ? `₹${Number(value).toLocaleString('en-IN')}` : value, name]}
        />
        <Bar dataKey="amount" radius={[4, 4, 0, 0]} maxBarSize={50}>
          {buckets.map((_, i) => (
            <Cell key={i} fill={SEQUENTIAL_BLUE[Math.min(i, SEQUENTIAL_BLUE.length - 1)]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
