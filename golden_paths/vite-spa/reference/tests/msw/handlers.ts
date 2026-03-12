import { http, HttpResponse } from "msw"

export const handlers = [
  // Example: mock your API base URL
  http.get("*/api/health", () => {
    return HttpResponse.json({ status: "ok" })
  }),
]
