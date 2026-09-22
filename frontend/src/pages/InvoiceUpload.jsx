import { CheckCircle2, Loader2, Upload, XCircle } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FileUploader from '../components/invoices/FileUploader'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Select from '../components/ui/Select'
import { useToast } from '../context/ToastContext'
import { extractErrorMessage } from '../services/api'
import { invoicesApi } from '../services/invoices'

const DEPARTMENTS = ['Finance', 'Operations', 'IT', 'Marketing', 'HR', 'Procurement']

export default function InvoiceUpload() {
  const [files, setFiles] = useState([])
  const [department, setDepartment] = useState('')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const toast = useToast()
  const navigate = useNavigate()

  const handleUpload = async () => {
    if (files.length === 0) return
    setUploading(true)
    setProgress(0)
    setResult(null)
    try {
      const { data } = await invoicesApi.upload(files, department, setProgress)
      setResult(data)
      if (data.created?.length) {
        toast.success(`${data.created.length} invoice(s) uploaded and processed.`)
      }
      if (data.errors?.length) {
        toast.warning(`${data.errors.length} file(s) failed validation.`)
      }
      setFiles([])
    } catch (error) {
      toast.error(extractErrorMessage(error))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-semibold text-slate-800 mb-1">Upload Invoices</h1>
      <p className="text-sm text-slate-500 mb-6">
        Drop one or more invoices below. Each file is stored, run through OCR extraction, and prepared for review.
      </p>

      <Card>
        <FileUploader files={files} onFilesChange={setFiles} disabled={uploading} />

        <div className="mt-5 grid sm:grid-cols-2 gap-4">
          <Select
            label="Department (optional)"
            placeholder="Select department"
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            options={DEPARTMENTS.map((d) => ({ label: d, value: d }))}
            disabled={uploading}
          />
        </div>

        {uploading && (
          <div className="mt-4">
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-blue-600 transition-all" style={{ width: `${progress}%` }} />
            </div>
            <p className="text-xs text-slate-400 mt-1.5 flex items-center gap-1.5">
              <Loader2 size={12} className="animate-spin" /> Uploading and running OCR extraction ({progress}%)...
            </p>
          </div>
        )}

        <div className="mt-5 flex justify-end">
          <Button icon={Upload} onClick={handleUpload} loading={uploading} disabled={files.length === 0}>
            Upload {files.length > 0 ? `(${files.length})` : ''}
          </Button>
        </div>
      </Card>

      {result && (
        <Card title="Processing results" className="mt-5">
          <ul className="space-y-2">
            {result.created?.map((inv) => (
              <li
                key={inv.id}
                className="flex items-center gap-3 px-3 py-2.5 rounded-md border border-slate-200 hover:border-blue-300 cursor-pointer"
                onClick={() => navigate(`/invoices/${inv.id}`)}
              >
                <CheckCircle2 size={18} className="text-emerald-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-700 truncate">
                    {inv.invoice_number || inv.documents?.[0]?.file_name || 'Untitled invoice'}
                  </p>
                  <p className="text-xs text-slate-400">
                    OCR confidence: {inv.ocr_confidence != null ? `${inv.ocr_confidence}%` : '—'} (
                    {inv.ocr_confidence_level || 'n/a'}) &middot; Status: {inv.status}
                  </p>
                </div>
                <span className="text-xs text-blue-600 font-medium shrink-0">Review →</span>
              </li>
            ))}
            {result.errors?.map((err, idx) => (
              <li key={idx} className="flex items-center gap-3 px-3 py-2.5 rounded-md border border-red-100 bg-red-50">
                <XCircle size={18} className="text-red-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-red-700 truncate">{err.file}</p>
                  <p className="text-xs text-red-500">{err.error}</p>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
