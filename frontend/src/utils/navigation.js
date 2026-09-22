import {
  ClipboardCheck,
  FileStack,
  FileText,
  LayoutDashboard,
  ReceiptText,
  ScrollText,
  Settings,
  ShoppingCart,
  Users,
  Wallet,
} from 'lucide-react'

export const NAV_ITEMS = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Invoices', to: '/invoices', icon: FileText },
  { label: 'Vendors', to: '/vendors', icon: Users },
  { label: 'Purchase Orders', to: '/purchase-orders', icon: ShoppingCart },
  { label: 'Approvals', to: '/approvals', icon: ClipboardCheck },
  { label: 'Payments', to: '/payments', icon: Wallet },
  { label: 'Reports', to: '/reports', icon: FileStack },
  { label: 'Audit Logs', to: '/audit-logs', icon: ScrollText, roles: ['ADMIN', 'AUDITOR'] },
  { label: 'Settings', to: '/settings', icon: Settings, roles: ['ADMIN', 'AP_MANAGER'] },
]

export const INVOICE_TABS = [
  { label: 'All', value: '' },
  { label: 'Pending', value: 'PENDING_APPROVAL' },
  { label: 'Exceptions', value: 'EXCEPTION' },
  { label: 'Approved', value: 'APPROVED' },
  { label: 'Rejected', value: 'REJECTED' },
]

export const ROLE_LABELS = {
  ADMIN: 'Admin',
  AP_MANAGER: 'AP Manager',
  AP_PROCESSOR: 'AP Processor',
  APPROVER: 'Approver',
  FINANCE_MANAGER: 'Finance Manager',
  AUDITOR: 'Auditor',
}
