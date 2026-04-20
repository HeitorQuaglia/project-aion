import type { Probe } from '../lib/api'

export function ProbeChip({ probe }: { probe: Probe }) {
  const isLLM = probe.probe_type === 'llm_judge'
  return (
    <div className="flex items-start gap-2 text-xs">
      <span
        className={`shrink-0 rounded px-1.5 py-0.5 font-mono ${
          isLLM ? 'bg-purple-900/40 text-purple-300' : 'bg-cyan-900/40 text-cyan-300'
        }`}
      >
        {isLLM ? 'llm' : 'det'}
      </span>
      <span className="text-slate-400">{probe.description}</span>
    </div>
  )
}
