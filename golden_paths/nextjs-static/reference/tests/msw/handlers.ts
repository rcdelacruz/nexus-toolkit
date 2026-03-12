import { http, HttpResponse } from "msw"

export const handlers = [
  // Add route handlers here for external API calls your components make
  http.get("https://api.example.com/data", () => {
    return HttpResponse.json({ items: [] })
  }),
]
