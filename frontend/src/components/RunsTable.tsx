import { Link } from 'react-router'
import type { Run } from '../lib/api'
import { StatusBadge } from './StatusBadge'

function formatMs(ms: number) {
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms.toFixed(0)}ms`
}

function durationMs(run: Run): number | null {
  if (!run.started_at || !run.finished_at) return null
  return new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()
}

export function RunsTable({ runs }: { runs: Run[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="text-xs uppercase text-[--color-muted] border-b border-[--color-border]">
          <tr>
            <th className="pb-2 pr-4">Status</th>
            <th className="pb-2 pr-4">Run ID</th>
            <th className="pb-2 pr-4">Scenario</th>
            <th className="pb-2 pr-4">Model</th>
            <th className="pb-2 pr-4">Provider</th>
            <th className="pb-2 pr-4">Wall Time</th>
            <th className="pb-2">Tokens (in/out)</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[--color-border]">
          {runs.map((run) => {
            const dur = run.observation?.wall_time_ms ?? durationMs(run)
            const tokens = run.observation
              ? `${run.observation.input_tokens ?? '—'} / ${run.observation.output_tokens ?? '—'}`
              : '—'
            return (
              <tr key={run.id} className="hover:bg-white/5 transition-colors">
                <td className="py-2 pr-4">
                  <StatusBadge status={run.status} />
                </td>
                <td className="py-2 pr-4 font-mono text-xs">
                  <Link to={`/runs/${run.id}`} className="text-blue-400 hover:underline">
                    {run.id.slice(0, 8)}
                  </Link>
                </td>
                <td className="py-2 pr-4 font-mono text-xs text-[--color-muted]">
                  {run.scenario_id}
                </td>
                <td className="py-2 pr-4">{run.model_id}</td>
                <td className="py-2 pr-4 capitalize">{run.provider}</td>
                <td className="py-2 pr-4">{dur != null ? formatMs(dur) : '—'}</td>
                <td className="py-2 text-[--color-muted]">{tokens}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
