import { useQuery } from '@tanstack/react-query'
import { getRun, getRunsBySuite } from '../lib/api'
import { keys } from '../lib/queryKeys'

const ACTIVE = new Set(['pending', 'running'])

export function useSuiteRuns(suiteId: string) {
  return useQuery({
    queryKey: keys.suiteRuns(suiteId),
    queryFn: () => getRunsBySuite(suiteId),
    refetchInterval: (query) => {
      const runs = query.state.data
      if (!runs) return false
      return runs.some((r) => ACTIVE.has(r.status)) ? 2000 : false
    },
  })
}

export function useRun(id: string) {
  return useQuery({
    queryKey: keys.run(id),
    queryFn: () => getRun(id),
    refetchInterval: (query) => {
      const run = query.state.data
      if (!run) return false
      return ACTIVE.has(run.status) ? 2000 : false
    },
  })
}
