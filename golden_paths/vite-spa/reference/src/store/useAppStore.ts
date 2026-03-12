import { create } from "zustand"
import { devtools, persist } from "zustand/middleware"

interface AppState {
  theme: "light" | "dark" | "system"
  sidebarOpen: boolean
  setTheme: (theme: AppState["theme"]) => void
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        theme: "system",
        sidebarOpen: true,
        setTheme: (theme) => set({ theme }),
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        setSidebarOpen: (open) => set({ sidebarOpen: open }),
      }),
      { name: "app-store" },
    ),
  ),
)
