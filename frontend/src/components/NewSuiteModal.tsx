import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createSuite } from '../lib/api'
import type { SuiteCreate } from '../lib/api'
import { keys } from '../lib/queryKeys'

interface ScenarioDraft {
  id: string
  input: string
}

interface Props {
  onClose: () => void
}

function Field({
  label,
  value,
  onChange,
  multiline,
  placeholder,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  multiline?: boolean
  placeholder?: string
}) {
  const base =
    'w-full bg-[--color-background] border border-[--color-border] rounded px-3 py-2 text-sm text-slate-200 placeholder:text-[--color-muted] focus:outline-none focus:ring-1 focus:ring-blue-500'
  return (
    <div>
      <label className="block text-xs font-medium text-[--color-muted] mb-1">{label}</label>
      {multiline ? (
        <textarea
          rows={3}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={base}
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={base}
        />
      )}
    </div>
  )
}

export function NewSuiteModal({ onClose }: Props) {
  const qc = useQueryClient()
  const [id, setId] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [scenarios, setScenarios] = useState<ScenarioDraft[]>([])

  const mutation = useMutation({
    mutationFn: (body: SuiteCreate) => createSuite(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.suites() })
      onClose()
    },
  })

  function addScenario() {
    setScenarios((prev) => [...prev, { id: '', input: '' }])
  }

  function updateScenario(index: number, field: keyof ScenarioDraft, value: string) {
    setScenarios((prev) => prev.map((s, i) => (i === index ? { ...s, [field]: value } : s)))
  }

  function removeScenario(index: number) {
    setScenarios((prev) => prev.filter((_, i) => i !== index))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    mutation.mutate({
      id,
      name,
      description,
      scenarios: scenarios.map((s) => ({
        id: s.id,
        suite_id: id,
        input: s.input,
        probes: [],
        tags: {},
      })),
    })
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-2xl bg-[--color-surface] rounded-xl border border-[--color-border] shadow-2xl p-6 overflow-y-auto max-h-[90vh]">
        <h2 className="text-lg font-semibold text-white mb-5">New Suite</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="ID (slug)" value={id} onChange={setId} placeholder="my-suite-v1" />
          <Field label="Name" value={name} onChange={setName} placeholder="My Suite" />
          <Field
            label="Description"
            value={description}
            onChange={setDescription}
            multiline
            placeholder="Optional description…"
          />

          {scenarios.length > 0 && (
            <div className="space-y-3">
              <p className="text-xs font-medium text-[--color-muted] uppercase">Scenarios</p>
              {scenarios.map((s, i) => (
                <div
                  key={i}
                  className="rounded border border-[--color-border] bg-[--color-background] p-3 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[--color-muted]">Scenario {i + 1}</span>
                    <button
                      type="button"
                      onClick={() => removeScenario(i)}
                      className="text-xs text-red-400 hover:text-red-300"
                    >
                      Remove
                    </button>
                  </div>
                  <Field
                    label="ID"
                    value={s.id}
                    onChange={(v) => updateScenario(i, 'id', v)}
                    placeholder="scenario-id"
                  />
                  <Field
                    label="Input"
                    value={s.input}
                    onChange={(v) => updateScenario(i, 'input', v)}
                    multiline
                    placeholder="Prompt or instruction for the AI…"
                  />
                </div>
              ))}
            </div>
          )}

          <button
            type="button"
            onClick={addScenario}
            className="text-sm text-blue-400 hover:text-blue-300 hover:underline"
          >
            + Add scenario
          </button>

          {mutation.isError && (
            <p className="text-sm text-red-400">{String(mutation.error)}</p>
          )}

          <div className="flex justify-end gap-3 pt-2 border-t border-[--color-border]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending || !id || !name}
              className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 rounded text-white disabled:opacity-50 transition-colors"
            >
              {mutation.isPending ? 'Creating…' : 'Create Suite'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
