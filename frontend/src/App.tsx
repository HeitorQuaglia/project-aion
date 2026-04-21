import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { createBrowserRouter, RouterProvider } from 'react-router'
import SuiteList from './pages/SuiteList'
import SuiteDetail from './pages/SuiteDetail'
import RunsPage from './pages/RunsPage'
import RunDetail from './pages/RunDetail'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      retry: 1,
    },
  },
})

const router = createBrowserRouter([
  { path: '/',                element: <SuiteList /> },
  { path: '/suites/:id',      element: <SuiteDetail /> },
  { path: '/suites/:id/runs', element: <RunsPage /> },
  { path: '/runs/:id',        element: <RunDetail /> },
])

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
