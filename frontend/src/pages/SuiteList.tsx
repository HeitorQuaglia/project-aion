import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSuites } from '../lib/api'
import { keys } from '../lib/queryKeys'
import { SuiteCard } from '../components/SuiteCard'
import { NewSuiteModal } from '../components/NewSuiteModal'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorAlert } from '../components/ErrorAlert'
import { PageHeader } from '../components/PageHeader'

export default function SuiteList() {
  const [showModal, setShowModal] = useState(false)
  const { data: suites, isLoading, isError, error } = useQuery({
    queryKey: keys.suites(),
    queryFn: getSuites,
  })

  return (
    <div className="min-h-screen bg-[--color-background] text-slate-100">
      <div className="max-w-5xl mx-auto px-6 py-10">
        <PageHeader
          title="Suites"
          subtitle="Test suites for your AI system"
          action={
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-600 rounded text-sm text-white transition-colors"
            >
              + New Suite
            </button>
          }
        />

        {isLoading && <LoadingSpinner />}
        {isError && <ErrorAlert message={String(error)} />}

        {suites && (
          suites.length === 0 ? (
            <p className="text-[--color-muted] text-sm mt-8">
              No suites yet. Create one to get started.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {suites.map((s) => (
                <SuiteCard key={s.id} suite={s} />
              ))}
            </div>
          )
        )}

        {showModal && <NewSuiteModal onClose={() => setShowModal(false)} />}
      </div>
    </div>
  )
}
