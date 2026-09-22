import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-3">
      <p className="text-5xl font-bold text-slate-300">404</p>
      <p className="text-slate-500">Page not found</p>
      <Link to="/dashboard" className="text-blue-600 text-sm font-medium">
        Back to dashboard
      </Link>
    </div>
  )
}
