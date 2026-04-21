export function ErrorAlert({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-800/50 bg-red-950/30 px-4 py-3 text-sm text-red-300 mt-4">
      {message}
    </div>
  )
}
