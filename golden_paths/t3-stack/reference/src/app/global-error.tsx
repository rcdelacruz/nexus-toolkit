"use client"

import { useEffect } from "react"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <html>
      <body className="flex min-h-screen flex-col items-center justify-center gap-4 font-sans">
        <h2 className="text-xl font-semibold">Something went wrong</h2>
        <p className="text-sm text-gray-500">
          {error.digest ? `Error ID: ${error.digest}` : "A critical error occurred."}
        </p>
        <button
          onClick={reset}
          className="rounded-md bg-black px-4 py-2 text-sm text-white hover:bg-gray-800"
        >
          Try again
        </button>
      </body>
    </html>
  )
}
