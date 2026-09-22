import { Boxes, Loader2, Lock, User } from 'lucide-react'
import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import Button from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'

const DEMO_ACCOUNTS = [
  { role: 'Admin', username: 'admin', password: 'Admin@12345' },
  { role: 'AP Manager', username: 'ap.manager', password: 'Demo@12345' },
  { role: 'AP Processor', username: 'ap.processor', password: 'Demo@12345' },
  { role: 'Approver', username: 'approver', password: 'Demo@12345' },
  { role: 'Finance Manager', username: 'finance.manager', password: 'Demo@12345' },
  { role: 'Auditor', username: 'auditor', password: 'Demo@12345' },
]

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) {
    const dest = location.state?.from?.pathname || '/dashboard'
    return <Navigate to={dest} replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    const result = await login(username, password)
    setLoading(false)
    if (result.success) {
      navigate('/dashboard')
    } else {
      setError(result.message || 'Invalid username or password.')
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-white rounded-xl shadow-2xl overflow-hidden grid md:grid-cols-2">
        <div className="hidden md:flex flex-col justify-between bg-gradient-to-br from-blue-700 to-slate-900 text-white p-8">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-white/10 rounded-lg">
              <Boxes size={22} />
            </div>
            <span className="font-semibold">AP Automation</span>
          </div>
          <div>
            <h2 className="text-2xl font-semibold leading-snug">
              Invoice capture to payment,
              <br /> fully automated.
            </h2>
            <p className="text-blue-100 text-sm mt-3">
              OCR extraction, validation, PO matching, approvals and payments — one platform.
            </p>
          </div>
          <p className="text-xs text-blue-200">&copy; {new Date().getFullYear()} AP Automation Demo</p>
        </div>

        <div className="p-8">
          <h1 className="text-xl font-semibold text-slate-800">Sign in to your account</h1>
          <p className="text-sm text-slate-500 mt-1">Enter your credentials to access the dashboard.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Username</label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoFocus
                  className="w-full pl-9 pr-3 py-2.5 rounded-md border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500"
                  placeholder="e.g. ap.manager"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-9 pr-3 py-2.5 rounded-md border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-md px-3 py-2">{error}</p>}

            <Button type="submit" size="lg" className="w-full" disabled={loading}>
              {loading ? <Loader2 size={16} className="animate-spin" /> : null}
              Sign in
            </Button>
          </form>

          <div className="mt-6 border-t border-slate-100 pt-4">
            <p className="text-xs font-medium text-slate-500 mb-2">Demo accounts (password shown for convenience)</p>
            <div className="grid grid-cols-2 gap-1.5">
              {DEMO_ACCOUNTS.map((acc) => (
                <button
                  type="button"
                  key={acc.username}
                  onClick={() => {
                    setUsername(acc.username)
                    setPassword(acc.password)
                  }}
                  className="text-left text-xs px-2 py-1.5 rounded border border-slate-200 hover:border-blue-400 hover:bg-blue-50 text-slate-600"
                >
                  <span className="font-medium block">{acc.role}</span>
                  <span className="text-slate-400">{acc.username}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
