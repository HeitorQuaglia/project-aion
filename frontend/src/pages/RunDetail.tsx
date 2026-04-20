import { useParams, Link } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import { useRun } from '../hooks/useRuns'
import { getSuite } from '../lib/api'
import { keys } from '../lib/queryKeys'
import { StatusBadge } from '../components/StatusBadge'
import { ProbeChip } from '../components/ProbeChip'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorAlert } from '../components/ErrorAlert'
import type { ReactNode } from 'react'

function KV({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium text-[--color-muted]">{label}</dt>
      <dd className="text-sm text-slate-200 mt-0.5">{value ?? '—'}</dd>
    </div>
  )
}

function formatMs(ms: number) {
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms.toFixed(0)}ms`
}

export default function RunDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: run, isLoading, isError, error } = useRun(id!)

  const { data: suite } = useQuery({
    queryKey: keys.suite(run?.suite_id ?? ''),
    queryFn: () => getSuite(run!.suite_id),
    enabled: !!run?.suite_id,
  })

  const scenario = suite?.scenarios.find((s) => s.id === run?.scenario_id)

  if (isLoading) return <LoadingSpinner fullPage />
  if (isError) return <ErrorAlert message={String(error)} />
  if (!run) return null

  const dur = run.observation?.wall_time_ms

  return (
    <div className="min-h-screen bg-[--color-background] text-slate-100">
      <div className="max-w-3xl mx-auto px-6 py-10 space-y-8">
        <div>
          <Link
            to={`/suites/${run.suite_id}/runs`}
            className="text-xs text-[--color-muted] hover:underline"
          >
            ← Runs
          </Link>
          <div className="flex items-center gap-3 mt-2">
            <h1 className="text-xl font-bold text-white font-mono">{run.id}</h1>
            <StatusBadge status={run.status} />
          </div>
        </div>

        <section className="rounded-xl border border-[--color-border] bg-[--color-surface] p-5">
          <dl className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <KV
              label="Suite"
              value={
                <Link
                  to={`/suites/${run.suite_id}`}
                  className="text-blue-400 hover:underline"
                >
                  {run.suite_id}
                </Link>
              }
            />
            <KV label="Scenario" value={run.scenario_id} />
            <KV label="Session" value={<span className="font-mono text-xs">{run.session_id}</span>} />
            <KV label="Model" value={run.model_id} />
            <KV label="Provider" value={run.provider} />
            <KV label="Wall Time" value={dur != null ? formatMs(dur) : null} />
            <KV label="Input Tokens" value={run.observation?.input_tokens} />
            <KV label="Output Tokens" value={run.observation?.output_tokens} />
            <KV
              label="Started"
              value={run.started_at ? new Date(run.started_at).toLocaleString() : null}
            />
            <KV
              label="Finished"
              value={run.finished_at ? new Date(run.finished_at).toLocaleString() : null}
            />
          </dl>
        </section>

        {run.observation?.error && (
          <section>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-red-400 mb-2">
              Error
            </h2>
            <pre className="text-xs text-red-300 bg-red-950/40 border border-red-800/40 rounded p-3 whitespace-pre-wrap">
              {run.observation.error}
            </pre>
          </section>
        )}

        {run.observation?.raw_response && (
          <section>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[--color-muted] mb-2">
              Raw Response
            </h2>
            <pre className="text-xs text-slate-300 bg-[--color-surface] border border-[--color-border] rounded p-4 whitespace-pre-wrap overflow-x-auto max-h-96 overflow-y-auto font-mono">
              {run.observation.raw_response}
            </pre>
          </section>
        )}

        {scenario && scenario.probes.length > 0 && (
          <section>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[--color-muted] mb-3">
              Probes ({scenario.probes.length})
            </h2>
            <ul className="space-y-2">
              {scenario.probes.map((p) => (
                <li
                  key={p.id}
                  className="rounded border border-[--color-border] bg-[--color-surface] px-3 py-2"
                >
                  <ProbeChip probe={p} />
                </li>
              ))}
            </ul>
          </section>
        )}

        {Object.keys(run.metadata).length > 0 && (
          <section>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[--color-muted] mb-2">
              Metadata
            </h2>
            <pre className="text-xs text-slate-400 bg-[--color-surface] border border-[--color-border] rounded p-3 whitespace-pre-wrap font-mono">
              {JSON.stringify(run.metadata, null, 2)}
            </pre>
          </section>
        )}
      </div>
    </div>
  )
}
