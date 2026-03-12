import { http, HttpResponse } from "msw"

export const handlers = [
  // Example handler — replace with real API routes
  http.get("/api/health", () => {
    return HttpResponse.json({ status: "ok" })
  }),
]
