export function LoadingSpinner({ fullPage }: { fullPage?: boolean }) {
  const spinner = (
    <div className="flex justify-center items-center py-12">
      <div className="w-6 h-6 rounded-full border-2 border-slate-600 border-t-blue-400 animate-spin" />
    </div>
  )
  if (fullPage) {
    return (
      <div className="min-h-screen bg-[--color-background] flex items-center justify-center">
        {spinner}
      </div>
    )
  }
  return spinner
}
