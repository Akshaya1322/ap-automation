import { Plus, Save, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import LoadingState from '../components/ui/LoadingState'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { extractErrorMessage } from '../services/api'
import { settingsApi } from '../services/settings'
import { ROLE_LABELS } from '../utils/navigation'

const ALL_ROLES = ['ADMIN', 'AP_MANAGER', 'AP_PROCESSOR', 'APPROVER', 'FINANCE_MANAGER', 'AUDITOR']

function ProfileSection() {
  const { user, refreshProfile } = useAuth()
  const toast = useToast()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '', department: '' })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (user) {
      setForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
        department: user.department || '',
      })
    }
  }, [user])

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await settingsApi.updateProfile(form)
      await refreshProfile()
      toast.success('Profile updated.')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card title="Profile">
      <form onSubmit={handleSave} className="grid sm:grid-cols-2 gap-4">
        <Input label="First Name" value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} />
        <Input label="Last Name" value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} />
        <Input label="Email" type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
        <Input label="Phone" value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
        <Input label="Department" value={form.department} onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))} />
        <Input label="Role" value={ROLE_LABELS[user?.role] || user?.role} disabled />
        <div className="sm:col-span-2 flex justify-end">
          <Button type="submit" icon={Save} loading={saving}>
            Save Profile
          </Button>
        </div>
      </form>
    </Card>
  )
}

function PasswordSection() {
  const toast = useToast()
  const [form, setForm] = useState({ old_password: '', new_password: '' })
  const [saving, setSaving] = useState(false)

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await settingsApi.changePassword(form)
      toast.success('Password changed successfully.')
      setForm({ old_password: '', new_password: '' })
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card title="Change Password">
      <form onSubmit={handleSave} className="grid sm:grid-cols-2 gap-4">
        <Input
          label="Current Password"
          type="password"
          required
          value={form.old_password}
          onChange={(e) => setForm((f) => ({ ...f, old_password: e.target.value }))}
        />
        <Input
          label="New Password"
          type="password"
          required
          value={form.new_password}
          onChange={(e) => setForm((f) => ({ ...f, new_password: e.target.value }))}
        />
        <div className="sm:col-span-2 flex justify-end">
          <Button type="submit" icon={Save} loading={saving}>
            Update Password
          </Button>
        </div>
      </form>
    </Card>
  )
}

function ApprovalMatrixSection() {
  const toast = useToast()
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await settingsApi.listMatrixRules()
      setRules((data.results || data).map((r) => ({ ...r })))
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const updateRule = (id, field, value) => {
    setRules((prev) => prev.map((r) => (r.id === id ? { ...r, [field]: value } : r)))
  }

  const toggleRole = (id, role) => {
    setRules((prev) =>
      prev.map((r) =>
        r.id === id
          ? { ...r, required_roles: r.required_roles.includes(role) ? r.required_roles.filter((x) => x !== role) : [...r.required_roles, role] }
          : r
      )
    )
  }

  const saveRule = async (rule) => {
    setSaving(true)
    try {
      if (rule.id.startsWith('new-')) {
        const { id, ...payload } = rule
        const { data } = await settingsApi.createMatrixRule(payload)
        setRules((prev) => prev.map((r) => (r.id === id ? data : r)))
      } else {
        await settingsApi.updateMatrixRule(rule.id, {
          min_amount: rule.min_amount,
          max_amount: rule.max_amount || null,
          required_roles: rule.required_roles,
          is_active: rule.is_active,
        })
      }
      toast.success('Approval matrix rule saved.')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const deleteRule = async (rule) => {
    if (rule.id.startsWith('new-')) {
      setRules((prev) => prev.filter((r) => r.id !== rule.id))
      return
    }
    try {
      await settingsApi.deleteMatrixRule(rule.id)
      setRules((prev) => prev.filter((r) => r.id !== rule.id))
      toast.success('Rule deleted.')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }

  const addRule = () => {
    setRules((prev) => [...prev, { id: `new-${Date.now()}`, min_amount: '0', max_amount: '', required_roles: ['AP_MANAGER'], is_active: true }])
  }

  if (loading) return <LoadingState label="Loading approval matrix..." />

  return (
    <Card
      title="Approval Matrix"
      actions={
        <Button size="sm" variant="secondary" icon={Plus} onClick={addRule}>
          Add Band
        </Button>
      }
    >
      <p className="text-xs text-slate-400 mb-4">
        Configure which roles must approve an invoice based on its total amount. Rules apply in ascending order of min amount.
      </p>
      <div className="space-y-4">
        {rules.map((rule) => (
          <div key={rule.id} className="border border-slate-200 rounded-md p-4">
            <div className="grid sm:grid-cols-2 gap-3 mb-3">
              <Input
                label="Min Amount"
                type="number"
                value={rule.min_amount}
                onChange={(e) => updateRule(rule.id, 'min_amount', e.target.value)}
              />
              <Input
                label="Max Amount (blank = unbounded)"
                type="number"
                value={rule.max_amount ?? ''}
                onChange={(e) => updateRule(rule.id, 'max_amount', e.target.value)}
              />
            </div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Required Approver Roles (in order)</label>
            <div className="flex flex-wrap gap-2 mb-3">
              {ALL_ROLES.map((role) => (
                <button
                  key={role}
                  type="button"
                  onClick={() => toggleRole(rule.id, role)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                    rule.required_roles.includes(role)
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-blue-300'
                  }`}
                >
                  {ROLE_LABELS[role]}
                </button>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" icon={Trash2} onClick={() => deleteRule(rule)}>
                Delete
              </Button>
              <Button size="sm" icon={Save} loading={saving} onClick={() => saveRule(rule)}>
                Save
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

export default function Settings() {
  const { user } = useAuth()
  const canManageMatrix = ['ADMIN', 'AP_MANAGER'].includes(user?.role)

  return (
    <div className="max-w-2xl space-y-5">
      <h1 className="text-xl font-semibold text-slate-800">Settings</h1>
      <ProfileSection />
      <PasswordSection />
      {canManageMatrix && <ApprovalMatrixSection />}
    </div>
  )
}
