import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'
import clsx from 'clsx'

export default function Table({ columns, data, sortKey, sortDir, onSort, rowKey = 'id', onRowClick }) {
  return (
    <div className="overflow-x-auto table-scroll">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200">
            {columns.map((col) => (
              <th
                key={col.key}
                className={clsx(
                  'text-left font-medium text-slate-500 px-4 py-2.5 whitespace-nowrap select-none',
                  col.sortable && 'cursor-pointer hover:text-slate-700'
                )}
                onClick={() => col.sortable && onSort?.(col.key)}
              >
                <span className="inline-flex items-center gap-1">
                  {col.header}
                  {col.sortable &&
                    (sortKey === col.key ? (
                      sortDir === 'asc' ? (
                        <ArrowUp size={12} />
                      ) : (
                        <ArrowDown size={12} />
                      )
                    ) : (
                      <ArrowUpDown size={12} className="opacity-30" />
                    ))}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={row[rowKey]}
              className={clsx(
                'border-b border-slate-100 last:border-0',
                onRowClick && 'cursor-pointer hover:bg-slate-50'
              )}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3 text-slate-700 whitespace-nowrap">
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
