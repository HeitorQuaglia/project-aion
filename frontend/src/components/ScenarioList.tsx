import { useState } from 'react'
import type { Scenario } from '../lib/api'
import { ProbeChip } from './ProbeChip'

export function ScenarioList({ scenarios }: { scenarios: Scenario[] }) {
  const [open, setOpen] = useState<Set<string>>(new Set())

  const toggle = (id: string) =>
    setOpen((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })

  return (
    <ul className="space-y-1">
      {scenarios.map((s) => (
        <li key={s.id} className="rounded border border-[--color-border] overflow-hidden">
          <button
            onClick={() => toggle(s.id)}
            className="w-full flex items-center justify-between px-4 py-2 text-sm text-left bg-[--color-surface] hover:bg-white/5 transition-colors"
          >
            <span className="font-mono text-xs text-slate-300">{s.id}</span>
            <span className="text-[--color-muted] text-xs">
              {s.probes.length} probe{s.probes.length !== 1 ? 's' : ''}
              <span className="ml-2">{open.has(s.id) ? '▲' : '▼'}</span>
            </span>
          </button>
          {open.has(s.id) && (
            <div className="px-4 py-3 bg-[--color-background] space-y-3 border-t border-[--color-border]">
              <div>
                <p className="text-xs font-medium text-[--color-muted] mb-1">INPUT</p>
                <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono bg-[--color-surface] rounded p-2">
                  {s.input}
                </pre>
              </div>
              {s.probes.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-[--color-muted] mb-2">PROBES</p>
                  <ul className="space-y-1">
                    {s.probes.map((p) => (
                      <li key={p.id}>
                        <ProbeChip probe={p} />
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {Object.keys(s.tags).length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {Object.entries(s.tags).map(([k, v]) => (
                    <span key={k} className="text-xs bg-slate-800 text-slate-400 rounded px-2 py-0.5">
                      {k}={v}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </li>
      ))}
    </ul>
  )
}
