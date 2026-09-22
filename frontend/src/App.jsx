import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/layout/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import AppLayout from './layouts/AppLayout'
import ApprovalDetail from './pages/ApprovalDetail'
import Approvals from './pages/Approvals'
import AuditLogs from './pages/AuditLogs'
import Dashboard from './pages/Dashboard'
import InvoiceDetail from './pages/InvoiceDetail'
import InvoiceUpload from './pages/InvoiceUpload'
import Invoices from './pages/Invoices'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import PaymentDetail from './pages/PaymentDetail'
import Payments from './pages/Payments'
import PurchaseOrderDetail from './pages/PurchaseOrderDetail'
import PurchaseOrders from './pages/PurchaseOrders'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import VendorDetail from './pages/VendorDetail'
import VendorForm from './pages/VendorForm'
import Vendors from './pages/Vendors'

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />

                <Route path="/invoices" element={<Invoices />} />
                <Route path="/invoices/upload" element={<InvoiceUpload />} />
                <Route path="/invoices/:id" element={<InvoiceDetail />} />

                <Route path="/vendors" element={<Vendors />} />
                <Route path="/vendors/new" element={<VendorForm />} />
                <Route path="/vendors/:id" element={<VendorDetail />} />
                <Route path="/vendors/:id/edit" element={<VendorForm />} />

                <Route path="/purchase-orders" element={<PurchaseOrders />} />
                <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />

                <Route path="/approvals" element={<Approvals />} />
                <Route path="/approvals/:id" element={<ApprovalDetail />} />

                <Route path="/payments" element={<Payments />} />
                <Route path="/payments/:id" element={<PaymentDetail />} />

                <Route path="/reports" element={<Reports />} />
                <Route path="/audit-logs" element={<AuditLogs />} />
                <Route path="/settings" element={<Settings />} />
              </Route>
            </Route>

            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}
