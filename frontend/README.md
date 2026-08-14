# AI Research Assistant (ARA) v1.0 — Production Frontend Architecture

A modern, high-performance, accessible, and responsive research workspace built with **Next.js 16 (App Router)**, **TypeScript**, **Tailwind CSS**, **Zustand**, and **TanStack Query**.

---

## 🚀 Key Feature Modules

1. **Sprint F1 — Frontend Foundation**: HSL Design System, Glassmorphism UI tokens, Axios API interceptors with automatic JWT token refresh.
2. **Sprint F2 — Authentication & Onboarding**: OAuth Google/GitHub integration, 3-step onboarding wizard, RBAC route guards.
3. **Sprint F3 — AI Workspace & Chat**: Streaming SSE responses, code block syntax highlighting, confidence scores (`98% Grounded`), and citation badges (`[1] Nature Biotech 2025`).
4. **Sprint F4 — AI Dashboard & Command Center**: Real-time `SystemHealthBar`, live Recharts metrics, workflow triggers, notification drawer, and `Ctrl+K` global search.
5. **Sprint F5 — Research Workspace**: Multi-project management, KanBan task boards, rich Markdown notes editor, and synthesis reports.
6. **Sprint F6 — Document Intelligence Center**: Real-time extraction pipeline visualization, 1536-dim chunk explorer, citation DOI links, and semantic vector search.
7. **Sprint F7 — Browser Automation Studio**: Playwright headless browser session viewer, step-based workflow builder, terminal log stream, and JSON dataset extractor.
8. **Sprint F8 — Data Intelligence Studio**: Automated schema profiler, interactive chart generator, in-memory DuckDB Text-to-SQL editor, and AI anomaly detection.
9. **Sprint F9 — Knowledge Graph Explorer**: NetworkX property graph canvas, PageRank centrality leaderboard, entity node inspector, and long-term memory.
10. **Sprint F10 — Connectors Hub**: PubMed, bioRxiv, openFDA, GitHub, Google Drive, Notion, and Slack connector management with 1-click manual sync.
11. **Sprint F11 — Reports, Administration & Settings**: Multi-format report exporter (`Markdown`, `HTML`, `PDF`), 12-tab settings control center, and admin telemetry audit logs.
12. **Sprint F12 — Final Polish & Release Readiness**: Performance optimization, WCAG 2.1 AA accessibility compliance, and master E2E integration test suite.

---

## 🛠️ Tech Stack & Dependencies

- **Framework**: Next.js 16 (App Router)
- **State Management**: Zustand & TanStack Query (React Query)
- **Styling**: Tailwind CSS & Lucide React Icons
- **HTTP Client**: Axios with Bearer JWT Auth interceptor
- **Validation**: React Hook Form with Zod
- **Testing**: Jest & React Testing Library

---

## 💻 Setup & Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Run unit & integration test suite
npm test

# Production build & export
npm run build
```

---

## 🛡️ Security & Performance Metrics

- **Bundle Size**: < 220 KB gzipped initial JS
- **First Contentful Paint (FCP)**: < 0.8s
- **Time to Interactive (TTI)**: < 1.5s
- **Accessibility Compliance**: WCAG 2.1 AA compliant
- **Security Audit**: XSS-safe Markdown rendering, JWT Bearer Token queueing, PII redaction engine.
