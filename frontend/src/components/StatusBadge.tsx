import type { RunStatus } from '../lib/api'

const CONFIG: Record<RunStatus, { label: string; classes: string }> = {
  pending:  { label: 'Pending',  classes: 'bg-yellow-900/40 text-yellow-300 ring-yellow-700/50' },
  running:  { label: 'Running',  classes: 'bg-blue-900/40   text-blue-300   ring-blue-700/50'   },
  complete: { label: 'Complete', classes: 'bg-green-900/40  text-green-300  ring-green-700/50'  },
  failed:   { label: 'Failed',   classes: 'bg-red-900/40    text-red-300    ring-red-700/50'    },
}

export function StatusBadge({ status }: { status: RunStatus }) {
  const { label, classes } = CONFIG[status]
  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${classes}`}>
      {label}
    </span>
  )
}
