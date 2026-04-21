import { useParams, Link } from 'react-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSuite, triggerRun } from '../lib/api'
import { keys } from '../lib/queryKeys'
import { ScenarioList } from '../components/ScenarioList'
import { RunsTable } from '../components/RunsTable'
import { useSuiteRuns } from '../hooks/useRuns'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorAlert } from '../components/ErrorAlert'

export default function SuiteDetail() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()

  const { data: suite, isLoading, isError, error } = useQuery({
    queryKey: keys.suite(id!),
    queryFn: () => getSuite(id!),
  })

  const { data: runs } = useSuiteRuns(id!)

  const trigger = useMutation({
    mutationFn: () => triggerRun(id!),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.suiteRuns(id!) }),
  })

  if (isLoading) return <LoadingSpinner fullPage />
  if (isError) return <ErrorAlert message={String(error)} />
  if (!suite) return null

  return (
    <div className="min-h-screen bg-[--color-background] text-slate-100">
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-10">
        <div className="flex items-start justify-between">
          <div>
            <Link to="/" className="text-xs text-[--color-muted] hover:underline">
              ← Suites
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1">{suite.name}</h1>
            <p className="font-mono text-xs text-[--color-muted] mt-0.5">{suite.id}</p>
            {suite.description && (
              <p className="text-sm text-slate-400 mt-2 max-w-xl">{suite.description}</p>
            )}
          </div>
          <div className="flex gap-2 shrink-0">
            <Link
              to={`/suites/${id}/runs`}
              className="px-3 py-2 text-sm rounded border border-[--color-border] text-slate-300 hover:bg-white/5 transition-colors"
            >
              All Runs
            </Link>
            <button
              onClick={() => trigger.mutate()}
              disabled={trigger.isPending || suite.scenarios.length === 0}
              className="px-4 py-2 text-sm bg-blue-700 hover:bg-blue-600 rounded text-white disabled:opacity-40 transition-colors"
            >
              {trigger.isPending ? 'Triggering…' : 'Trigger Run'}
            </button>
          </div>
        </div>

        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[--color-muted] mb-3">
            Scenarios ({suite.scenarios.length})
          </h2>
          {suite.scenarios.length === 0 ? (
            <p className="text-sm text-[--color-muted]">No scenarios defined.</p>
          ) : (
            <ScenarioList scenarios={suite.scenarios} />
          )}
        </section>

        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[--color-muted]">
              Recent Runs
            </h2>
            <Link to={`/suites/${id}/runs`} className="text-xs text-blue-400 hover:underline">
              View all →
            </Link>
          </div>
          {runs && runs.length > 0 ? (
            <RunsTable runs={runs.slice(0, 10)} />
          ) : (
            <p className="text-sm text-[--color-muted]">No runs yet.</p>
          )}
        </section>
      </div>
    </div>
  )
}
