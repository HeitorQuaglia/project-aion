import { Link } from 'react-router'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Suite } from '../lib/api'
import { triggerRun } from '../lib/api'
import { keys } from '../lib/queryKeys'

export function SuiteCard({ suite }: { suite: Suite }) {
  const qc = useQueryClient()
  const trigger = useMutation({
    mutationFn: () => triggerRun(suite.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.suiteRuns(suite.id) }),
  })

  return (
    <div className="rounded-xl border border-[--color-border] bg-[--color-surface] p-5 flex flex-col gap-3">
      <div>
        <Link
          to={`/suites/${suite.id}`}
          className="text-white font-semibold hover:underline text-base"
        >
          {suite.name}
        </Link>
        <p className="font-mono text-xs text-[--color-muted] mt-0.5">{suite.id}</p>
      </div>
      {suite.description && (
        <p className="text-sm text-slate-400 line-clamp-2">{suite.description}</p>
      )}
      <div className="flex items-center justify-between mt-auto">
        <span className="text-xs text-[--color-muted]">
          {suite.scenarios.length} scenario{suite.scenarios.length !== 1 ? 's' : ''}
        </span>
        <div className="flex gap-2">
          <Link
            to={`/suites/${suite.id}/runs`}
            className="text-xs px-3 py-1.5 rounded border border-[--color-border] text-slate-300 hover:bg-white/5 transition-colors"
          >
            Runs
          </Link>
          <button
            onClick={() => trigger.mutate()}
            disabled={trigger.isPending || suite.scenarios.length === 0}
            className="text-xs px-3 py-1.5 rounded bg-blue-700 hover:bg-blue-600 text-white disabled:opacity-40 transition-colors"
          >
            {trigger.isPending ? 'Triggering…' : 'Trigger Run'}
          </button>
        </div>
      </div>
    </div>
  )
}
