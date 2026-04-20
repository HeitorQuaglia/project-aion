import { useParams, Link } from 'react-router'
import { useSuiteRuns } from '../hooks/useRuns'
import { RunsTable } from '../components/RunsTable'
import { LoadingSpinner } from '../components/LoadingSpinner'

export default function RunsPage() {
  const { id } = useParams<{ id: string }>()
  const { data: runs, isLoading } = useSuiteRuns(id!)

  const isPolling = runs?.some((r) => r.status === 'pending' || r.status === 'running') ?? false

  return (
    <div className="min-h-screen bg-[--color-background] text-slate-100">
      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <Link to={`/suites/${id}`} className="text-xs text-[--color-muted] hover:underline">
              ← Suite
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1">Runs</h1>
          </div>
          {isPolling && (
            <span className="flex items-center gap-2 text-xs text-blue-400">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              Live — polling every 2s
            </span>
          )}
        </div>

        {isLoading && <LoadingSpinner />}
        {!isLoading && runs?.length === 0 && (
          <p className="text-sm text-[--color-muted]">No runs yet.</p>
        )}
        {runs && runs.length > 0 && <RunsTable runs={runs} />}
      </div>
    </div>
  )
}
