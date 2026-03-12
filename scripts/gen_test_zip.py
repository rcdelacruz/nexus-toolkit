#!/usr/bin/env python3
"""
Generate a minimal test Figma Make ZIP and print a ready-to-paste
Claude Code prompt to test the full 5-tool pipeline.

Usage:
    python3 scripts/gen_test_zip.py
    python3 scripts/gen_test_zip.py --golden-path t3-stack --project-name my-saas
"""
import argparse
import base64
import io
import json
import zipfile

# ── Fake Figma Make file contents ──────────────────────────────────────────────

BUTTON = """\
import React from 'react';

const Button = ({ children, onClick, variant = 'primary' }) => {
  return (
    <button
      onClick={onClick}
      style={{
        backgroundColor: variant === 'primary' ? '#3B82F6' : '#6B7280',
        color: '#FFFFFF',
        padding: '8px 16px',
        borderRadius: '6px',
        border: 'none',
        fontFamily: 'Inter, sans-serif',
        fontSize: '14px',
        cursor: 'pointer',
      }}
    >
      {children}
    </button>
  );
};

export default Button;
"""

CARD = """\
import React from 'react';
import Button from './Button';

const Card = ({ title, description, imageUrl }) => {
  return (
    <div style={{
      backgroundColor: '#FFFFFF',
      border: '1px solid #E5E7EB',
      borderRadius: '12px',
      padding: '24px',
      maxWidth: '320px',
      fontFamily: 'Inter, sans-serif',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    }}>
      {imageUrl && <img src={imageUrl} alt={title} style={{ width: '100%', borderRadius: '8px' }} />}
      <h3 style={{ color: '#111827', fontSize: '18px', margin: '12px 0 8px' }}>{title}</h3>
      <p style={{ color: '#6B7280', fontSize: '14px', lineHeight: '1.5' }}>{description}</p>
      <Button>Learn More</Button>
    </div>
  );
};

export default Card;
"""

NAVBAR = """\
import React from 'react';

const Navbar = ({ brand, links = [] }) => {
  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 32px',
      backgroundColor: '#FFFFFF',
      borderBottom: '1px solid #E5E7EB',
      fontFamily: 'Inter, sans-serif',
    }}>
      <span style={{ fontSize: '20px', fontWeight: 700, color: '#111827' }}>{brand}</span>
      <ul style={{ display: 'flex', gap: '24px', listStyle: 'none', margin: 0, padding: 0 }}>
        {links.map((link) => (
          <li key={link.href}>
            <a href={link.href} style={{ color: '#4B5563', textDecoration: 'none', fontSize: '14px' }}>
              {link.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Navbar;
"""

HOME_PAGE = """\
import React from 'react';
import Navbar from '../components/Navbar';
import Card from '../components/Card';
import Button from '../components/Button';

const HomePage = () => {
  return (
    <div style={{ fontFamily: 'Inter, sans-serif', backgroundColor: '#F9FAFB', minHeight: '100vh' }}>
      <Navbar
        brand="MyApp"
        links={[
          { href: '/features', label: 'Features' },
          { href: '/pricing', label: 'Pricing' },
          { href: '/login', label: 'Login' },
        ]}
      />
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '64px 32px' }}>
        <h1 style={{ fontSize: '48px', fontWeight: 800, color: '#111827', textAlign: 'center' }}>
          Welcome to MyApp
        </h1>
        <p style={{ fontSize: '18px', color: '#6B7280', textAlign: 'center', margin: '16px 0 48px' }}>
          The next generation platform for your business
        </p>
        <div style={{ display: 'flex', gap: '24px', justifyContent: 'center' }}>
          <Card title="Feature One" description="Build faster with our tools" />
          <Card title="Feature Two" description="Scale effortlessly to millions" />
          <Card title="Feature Three" description="Collaborate across your team" />
        </div>
        <div style={{ textAlign: 'center', marginTop: '48px' }}>
          <Button>Get Started Free</Button>
        </div>
      </main>
    </div>
  );
};

export default HomePage;
"""

DASHBOARD_PAGE = """\
import React from 'react';
import Navbar from '../components/Navbar';

const DashboardPage = () => {
  return (
    <div style={{ fontFamily: 'Inter, sans-serif' }}>
      <Navbar brand="MyApp" links={[{ href: '/settings', label: 'Settings' }]} />
      <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, color: '#111827' }}>Dashboard</h1>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px', marginTop: '24px' }}>
          {['Total Users', 'Revenue', 'Active Projects'].map((metric) => (
            <div key={metric} style={{
              backgroundColor: '#FFFFFF',
              border: '1px solid #E5E7EB',
              borderRadius: '12px',
              padding: '24px',
            }}>
              <p style={{ color: '#6B7280', fontSize: '14px', margin: 0 }}>{metric}</p>
              <p style={{ color: '#111827', fontSize: '32px', fontWeight: 700, margin: '8px 0 0' }}>0</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
"""

GLOBALS_CSS = """\
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background-color: #F9FAFB;
  color: #111827;
}

:root {
  --color-primary: #3B82F6;
  --color-primary-dark: #2563EB;
  --color-gray-50: #F9FAFB;
  --color-gray-100: #F3F4F6;
  --color-gray-200: #E5E7EB;
  --color-gray-500: #6B7280;
  --color-gray-900: #111827;
  --color-white: #FFFFFF;
  --font-sans: 'Inter', sans-serif;
  --radius-md: 6px;
  --radius-lg: 12px;
}
"""


def build_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("components/Button.tsx", BUTTON)
        zf.writestr("components/Card.tsx", CARD)
        zf.writestr("components/Navbar.tsx", NAVBAR)
        zf.writestr("pages/home.tsx", HOME_PAGE)
        zf.writestr("pages/dashboard.tsx", DASHBOARD_PAGE)
        zf.writestr("styles/globals.css", GLOBALS_CSS)
    return buf.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a test Figma Make ZIP")
    parser.add_argument("--golden-path", default="nextjs-fullstack",
                        choices=["nextjs-fullstack", "nextjs-static", "t3-stack", "vite-spa", "monorepo"])
    parser.add_argument("--project-name", default="my-app")
    parser.add_argument("--save", metavar="PATH", help="Also save the ZIP to a file")
    args = parser.parse_args()

    zip_bytes = build_zip()
    zip_b64 = base64.b64encode(zip_bytes).decode()

    if args.save:
        with open(args.save, "wb") as f:
            f.write(zip_bytes)
        print(f"ZIP saved to: {args.save}")

    prompt = f"""\
Run the full Figma pipeline on this test ZIP:

1. Call `ingest_figma_zip` with:
   - zip_data: {zip_b64}
   - golden_path: {args.golden_path}
   - project_name: {args.project_name}

2. Pass the result to `analyze_code`

3. Pass the result to `extract_tokens`

4. Pass the result to `remap_to_golden_path`

5. Pass the result to `package_output`

After each step, briefly describe what was found/produced.
At the end, confirm the final ZIP size and file count.
"""

    print("=" * 70)
    print("COPY THIS PROMPT INTO CLAUDE CODE:")
    print("=" * 70)
    print(prompt)
    print("=" * 70)
    print(f"\nZIP stats: {len(zip_bytes)} bytes, b64 length: {len(zip_b64)} chars")


if __name__ == "__main__":
    main()
