/**
 * HTML sanitization for user-generated content.
 * Prevents XSS when rendering untrusted HTML with dangerouslySetInnerHTML.
 *
 * Usage:
 *   import { sanitizeHtml } from "@/lib/sanitize"
 *
 *   <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(userContent) }} />
 */

import DOMPurify from "isomorphic-dompurify"

/** Allowed HTML tags for rich text. Tighten or expand per your content policy. */
const ALLOWED_TAGS = [
  "b", "i", "em", "strong", "a", "p", "br",
  "ul", "ol", "li", "h1", "h2", "h3", "blockquote",
]

/** Allowed attributes. `rel` enforced on links to prevent tabnapping. */
const ALLOWED_ATTR = ["href", "rel"]

/**
 * Sanitize an untrusted HTML string.
 * Returns a safe string suitable for dangerouslySetInnerHTML.
 */
export function sanitizeHtml(dirty: string): string {
  return String(
    DOMPurify.sanitize(dirty, {
      ALLOWED_TAGS,
      ALLOWED_ATTR,
      FORBID_ATTR: ["style", "onerror", "onload"],
      FORCE_BODY: true,
    })
  )
}
