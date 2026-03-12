export type { Database } from "./types/database.js"

export { createSupabaseBrowserClient } from "./client/browser.js"
export { createSupabaseServerClient, createSupabaseAdminClient } from "./client/server.js"

export { signInWithEmail, signInWithGoogle, signOut, getUser, getSession } from "./helpers/auth.js"
export { getUserRole, hasPermission, ROLES } from "./helpers/rbac.js"
export { logAuditEvent } from "./helpers/audit.js"
export { subscribeToTable, unsubscribeFromTable } from "./helpers/realtime.js"
export { uploadFile, getPublicUrl, deleteFile } from "./helpers/storage.js"
