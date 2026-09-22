import { File as FileIcon, Upload, X } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'
import clsx from 'clsx'

const ACCEPTED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff']
const MAX_SIZE_MB = 15

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function FileUploader({ files, onFilesChange, disabled }) {
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  const validateAndAdd = useCallback(
    (fileList) => {
      const incoming = Array.from(fileList)
      const valid = []
      let errorMsg = ''

      for (const file of incoming) {
        const ext = '.' + file.name.split('.').pop().toLowerCase()
        if (!ACCEPTED_EXTENSIONS.includes(ext)) {
          errorMsg = `"${file.name}" is not a supported format (PDF, JPG, PNG, TIFF only).`
          continue
        }
        if (file.size > MAX_SIZE_MB * 1024 * 1024) {
          errorMsg = `"${file.name}" exceeds the ${MAX_SIZE_MB}MB limit.`
          continue
        }
        valid.push(file)
      }
      setError(errorMsg)
      if (valid.length) onFilesChange([...files, ...valid])
    },
    [files, onFilesChange]
  )

  const onDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    if (disabled) return
    validateAndAdd(e.dataTransfer.files)
  }

  const removeFile = (idx) => {
    onFilesChange(files.filter((_, i) => i !== idx))
  }

  return (
    <div>
      <div
        className={clsx(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
          dragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50',
          disabled && 'opacity-50 pointer-events-none'
        )}
        onDragOver={(e) => {
          e.preventDefault()
          setDragActive(true)
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS.join(',')}
          className="hidden"
          onChange={(e) => e.target.files && validateAndAdd(e.target.files)}
        />
        <div className="mx-auto w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
          <Upload size={22} />
        </div>
        <p className="text-sm font-medium text-slate-700">
          Drag & drop invoices here, or <span className="text-blue-600">browse</span>
        </p>
        <p className="text-xs text-slate-400 mt-1">PDF, JPG, JPEG, PNG, TIFF up to {MAX_SIZE_MB}MB each · multiple files supported</p>
      </div>

      {error && <p className="text-xs text-red-600 mt-2">{error}</p>}

      {files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((file, idx) => (
            <li
              key={`${file.name}-${idx}`}
              className="flex items-center gap-3 px-3 py-2 rounded-md border border-slate-200 bg-white text-sm"
            >
              <FileIcon size={16} className="text-slate-400 shrink-0" />
              <span className="flex-1 truncate text-slate-700">{file.name}</span>
              <span className="text-xs text-slate-400 shrink-0">{formatSize(file.size)}</span>
              {!disabled && (
                <button
                  type="button"
                  onClick={() => removeFile(idx)}
                  className="text-slate-400 hover:text-red-500 shrink-0"
                >
                  <X size={15} />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
