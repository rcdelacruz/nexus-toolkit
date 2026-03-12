import type { NextConfig } from "next"

// Security headers are not supported with `output: "export"`.
// Set these at your hosting/CDN layer instead:
//
// Vercel — vercel.json:
//   { "headers": [{ "source": "/(.*)", "headers": [...] }] }
//
// Cloudflare Pages — _headers file in /public:
//   /*
//     X-Frame-Options: SAMEORIGIN
//     X-Content-Type-Options: nosniff
//     Referrer-Policy: strict-origin-when-cross-origin
//     Permissions-Policy: camera=(), microphone=(), geolocation=()
//     Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
//
// Nginx — in server block:
//   add_header X-Frame-Options "SAMEORIGIN";
//   add_header X-Content-Type-Options "nosniff";
//   add_header Referrer-Policy "strict-origin-when-cross-origin";

const nextConfig: NextConfig = {
  output: "export",
}

export default nextConfig
