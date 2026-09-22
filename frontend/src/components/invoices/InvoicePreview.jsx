import { FileWarning } from 'lucide-react'

export default function InvoicePreview({ document }) {
  if (!document) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[420px] text-slate-400 gap-2">
        <FileWarning size={28} />
        <p className="text-sm">No document available.</p>
      </div>
    )
  }

  const isPdf = document.file_type === 'pdf'

  return (
    <div className="h-full min-h-[420px] bg-slate-100 rounded-md overflow-hidden">
      {isPdf ? (
        <iframe title={document.file_name} src={document.file_url} className="w-full h-full min-h-[560px]" />
      ) : (
        <img src={document.file_url} alt={document.file_name} className="w-full h-auto" />
      )}
    </div>
  )
}
