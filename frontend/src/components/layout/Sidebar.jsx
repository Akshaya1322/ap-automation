import clsx from 'clsx'
import { Boxes, X } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { NAV_ITEMS } from '../../utils/navigation'

export default function Sidebar({ mobileOpen, onClose }) {
  const { user } = useAuth()

  const items = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes(user?.role))

  const content = (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-5 h-16 shrink-0 border-b border-slate-800">
        <div className="p-1.5 bg-blue-600 rounded-md">
          <Boxes size={18} className="text-white" />
        </div>
        <span className="text-white font-semibold text-sm tracking-wide">AP Automation</span>
        <button className="ml-auto lg:hidden text-slate-400" onClick={onClose}>
          <X size={20} />
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onClose}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              )
            }
          >
            <item.icon size={17} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-4 text-xs text-slate-500 border-t border-slate-800">
        AP Automation v1.0 &middot; Demo
      </div>
    </div>
  )

  return (
    <>
      <aside className="hidden lg:flex lg:flex-col w-64 shrink-0 bg-slate-900 h-screen sticky top-0">
        {content}
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/60" onClick={onClose} />
          <aside className="relative w-64 h-full bg-slate-900">{content}</aside>
        </div>
      )}
    </>
  )
}
