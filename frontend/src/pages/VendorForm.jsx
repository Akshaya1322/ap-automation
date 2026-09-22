import { ArrowLeft, Save } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import LoadingState from '../components/ui/LoadingState'
import Select from '../components/ui/Select'
import { useToast } from '../context/ToastContext'
import { extractErrorMessage } from '../services/api'
import { vendorsApi } from '../services/vendors'

const CATEGORIES = ['Office Supplies', 'IT Services', 'Logistics', 'Facility Management', 'Manufacturing', 'Marketing', 'Consulting', 'Catering', 'Construction', 'Hardware', 'Other']
const STATES = ['Maharashtra', 'Karnataka', 'Gujarat', 'Delhi', 'Tamil Nadu', 'West Bengal', 'Haryana', 'Other']

const EMPTY = {
  name: '',
  code: '',
  gstin: '',
  pan: '',
  email: '',
  phone: '',
  contact_person: '',
  address_line1: '',
  address_line2: '',
  city: '',
  state: '',
  pincode: '',
  country: 'India',
  category: '',
  department: '',
  payment_terms_days: 30,
  bank_details: { account_holder_name: '', account_number: '', bank_name: '', ifsc_code: '', branch: '' },
}

export default function VendorForm() {
  const { id } = useParams()
  const isEdit = !!id
  const navigate = useNavigate()
  const toast = useToast()
  const [form, setForm] = useState(EMPTY)
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (!isEdit) return
    vendorsApi
      .get(id)
      .then(({ data }) => {
        setForm({
          ...EMPTY,
          ...data,
          bank_details: data.bank_details
            ? { account_holder_name: data.bank_details.account_holder_name, account_number: '', bank_name: data.bank_details.bank_name, ifsc_code: data.bank_details.ifsc_code, branch: data.bank_details.branch }
            : EMPTY.bank_details,
        })
      })
      .catch((err) => toast.error(extractErrorMessage(err)))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const setField = (name, value) => setForm((prev) => ({ ...prev, [name]: value }))
  const setBankField = (name, value) => setForm((prev) => ({ ...prev, bank_details: { ...prev.bank_details, [name]: value } }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setErrors({})
    try {
      const payload = { ...form }
      if (!payload.bank_details.account_number) delete payload.bank_details
      if (isEdit) {
        await vendorsApi.update(id, payload)
        toast.success('Vendor updated.')
      } else {
        const { data } = await vendorsApi.create(payload)
        toast.success('Vendor created as draft.')
        navigate(`/vendors/${data.id}`)
        return
      }
      navigate(`/vendors/${id}`)
    } catch (err) {
      const data = err?.response?.data
      if (data?.errors) setErrors(data.errors)
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingState label="Loading vendor..." />

  return (
    <div className="max-w-3xl">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-3"
      >
        <ArrowLeft size={15} /> Back
      </button>
      <h1 className="text-xl font-semibold text-slate-800 mb-5">{isEdit ? 'Edit Vendor' : 'New Vendor'}</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <Card title="Company Information">
          <div className="grid sm:grid-cols-2 gap-4">
            <Input label="Vendor Name" required value={form.name} onChange={(e) => setField('name', e.target.value)} error={errors.name} />
            <Input label="Vendor Code" required value={form.code} onChange={(e) => setField('code', e.target.value)} error={errors.code} disabled={isEdit} />
            <Input label="GSTIN" value={form.gstin} onChange={(e) => setField('gstin', e.target.value.toUpperCase())} error={errors.gstin} />
            <Input label="PAN" value={form.pan} onChange={(e) => setField('pan', e.target.value.toUpperCase())} />
            <Select label="Category" placeholder="Select category" options={CATEGORIES.map((c) => ({ label: c, value: c }))} value={form.category} onChange={(e) => setField('category', e.target.value)} />
            <Input label="Payment Terms (days)" type="number" value={form.payment_terms_days} onChange={(e) => setField('payment_terms_days', Number(e.target.value))} />
          </div>
        </Card>

        <Card title="Contact Details">
          <div className="grid sm:grid-cols-2 gap-4">
            <Input label="Contact Person" value={form.contact_person} onChange={(e) => setField('contact_person', e.target.value)} />
            <Input label="Email" type="email" value={form.email} onChange={(e) => setField('email', e.target.value)} error={errors.email} />
            <Input label="Phone" value={form.phone} onChange={(e) => setField('phone', e.target.value)} />
            <Input label="Department" value={form.department} onChange={(e) => setField('department', e.target.value)} />
            <Input label="Address Line 1" className="sm:col-span-2" value={form.address_line1} onChange={(e) => setField('address_line1', e.target.value)} />
            <Input label="Address Line 2" className="sm:col-span-2" value={form.address_line2} onChange={(e) => setField('address_line2', e.target.value)} />
            <Input label="City" value={form.city} onChange={(e) => setField('city', e.target.value)} />
            <Select label="State" placeholder="Select state" options={STATES.map((s) => ({ label: s, value: s }))} value={form.state} onChange={(e) => setField('state', e.target.value)} />
            <Input label="Pincode" value={form.pincode} onChange={(e) => setField('pincode', e.target.value)} />
            <Input label="Country" value={form.country} onChange={(e) => setField('country', e.target.value)} />
          </div>
        </Card>

        <Card title="Bank Details" padded>
          <p className="text-xs text-slate-400 mb-3">Sensitive — stored securely and masked everywhere except this form.</p>
          <div className="grid sm:grid-cols-2 gap-4">
            <Input label="Account Holder Name" value={form.bank_details.account_holder_name} onChange={(e) => setBankField('account_holder_name', e.target.value)} />
            <Input label="Account Number" value={form.bank_details.account_number} onChange={(e) => setBankField('account_number', e.target.value)} placeholder={isEdit ? 'Leave blank to keep unchanged' : ''} />
            <Input label="Bank Name" value={form.bank_details.bank_name} onChange={(e) => setBankField('bank_name', e.target.value)} />
            <Input label="IFSC Code" value={form.bank_details.ifsc_code} onChange={(e) => setBankField('ifsc_code', e.target.value.toUpperCase())} />
            <Input label="Branch" value={form.bank_details.branch} onChange={(e) => setBankField('branch', e.target.value)} />
          </div>
        </Card>

        <div className="flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={() => navigate(-1)}>
            Cancel
          </Button>
          <Button type="submit" icon={Save} loading={saving}>
            {isEdit ? 'Save Changes' : 'Create Vendor'}
          </Button>
        </div>
      </form>
    </div>
  )
}
