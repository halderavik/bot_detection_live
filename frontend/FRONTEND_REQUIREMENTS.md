# Frontend Requirements & Setup Guide

## Table of Contents
1. [Overview](#overview)
2. [Pages and Navigation](#pages-and-navigation)
3. [Core Dependencies](#core-dependencies)
4. [Development Dependencies](#development-dependencies)
5. [Project Structure](#project-structure)
6. [Configuration Files](#configuration-files)
7. [Installation & Setup](#installation--setup)
8. [Development Workflow](#development-workflow)
9. [Build & Deployment](#build--deployment)
10. [Testing](#testing)
11. [Code Quality](#code-quality)
12. [Browser Support](#browser-support)
13. [Performance Features](#performance-features)
14. [Troubleshooting](#troubleshooting)

---

## Overview

The Bot Detection Frontend is a React dashboard built with Vite and Tailwind CSS. It shows bot and quality results for survey sessions, adds tracking to Decipher surveys, and holds the service settings.

### Layout
- **Wide screens:** a grouped left sidebar with the service status at the bottom (checked against `/health` every minute: running, degraded or unreachable).
- **Phones and narrow screens (below the `lg` breakpoint):** a top bar with a menu button that opens the same navigation as a slide-out panel. It closes on navigation or Escape. Pages use a 16px side gutter on phones.
- Frame: `src/components/layout/AppShell.jsx` (the navigation groups are defined there as `NAV_GROUPS`).

### Addresses
- **Production** is a static page in a storage bucket, which cannot send every path to `index.html`, so addresses use a hash: `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html#/quality`. This is switched on by `VITE_ROUTER_MODE=hash` in `frontend/.env.production`, which makes `App.jsx` use `HashRouter`.
- **Local development** uses normal paths (`BrowserRouter`), for example `http://localhost:3000/quality`.

### Removed
These were removed because they showed made-up or non-working content: hard-coded "from last week" trends, the random "Test Webhook" result, made-up integration logs, the fixed "Production Ready" badge, the mocked session comparison, the non-working dark-mode toggle, and Settings options that nothing used (notifications, data retention, debug mode, per-method switches, min events).

---

## Pages and Navigation

### Sidebar groups

| Group | Page | Route | Component |
|-------|------|-------|-----------|
| Monitor | Overview | `/` | `Overview.jsx` |
| Monitor | Live Quality | `/quality` | `LiveQuality.jsx` (+ `quality/*`) |
| Monitor | Sessions | `/sessions` | `SessionList.jsx` |
| Analyse | Open-end quality | `/text-analysis` | `TextAnalysis.jsx` |
| Analyse | Reports | `/reports` | `ReportBuilder.jsx` |
| Set up | Add tracking | `/tracking` | `SurveyTracking.jsx` |
| Set up | Integrations | `/integrations` | `Integrations.jsx` |
| Set up | Settings | `/settings` | `Settings.jsx` |
| Developers | Quick start | `/quick-start` | `QuickStartGuide.jsx` |
| Developers | API playground | `/api-playground` | `ApiPlayground.jsx` |

### Detail routes
- `/sessions/:sessionId` - Session details (`SessionDetails.jsx`)
- `/surveys/:surveyId` - Survey details (`SurveyDetails.jsx`)
- `/surveys/:surveyId/platforms/:platformId` - Platform details (`PlatformDetails.jsx`)
- `/surveys/:surveyId/platforms/:platformId/respondents/:respondentId` - Respondent details (`RespondentDetails.jsx`)
- `/surveys/:surveyId/platforms/:platformId/respondents/:respondentId/sessions/:sessionId` - Session details
- `/dashboard` and `/surveys` redirect to `/` (the Overview replaced the old Dashboard and Surveys list).
- Any other path shows a "This page doesn't exist" view with a link back to the Overview.

### What each page does
- **Overview:** last-7-days tiles (sessions, checked, bots with bot rate, surveys), a surveys table with bot rate and links to Live Quality, a chart of starts and bots per day over 14 days, and the latest bots. Bot rate everywhere is sessions judged bots divided by sessions checked.
- **Live Quality:** pick a survey (tracked surveys first; also opened with `?survey=<id>`). Shows totals, flag counts, quality distribution, trend and one row per respondent under that survey's rules. Rules can be edited per survey (`quality/QualityRules.jsx`), results exported as CSV, and **Add flags to a data file** (`quality/QualityDataFile.jsx`) returns an uploaded `.sav`, `.csv` or `.xlsx` file with `LQ_` variables added.
- **Sessions:** latest verdict, risk, bot score, platform and event count per session. Filters (verdict, risk, platform, search) are kept in the URL; results are paginated.
- **Session details:** the verdict and the signals that decided it first, then behaviour scores with plain labels, session facts (time in survey, browser, IP), fraud checks, open ends, grid, timing, and collapsible event log and raw analysis output.
- **Open-end quality:** text quality results for open-ended answers.
- **Reports:** report builder for summary and detailed reports, including text quality figures.
- **Add tracking:** upload a Decipher survey XML (up to 5 MB), choose the privacy notice and the early end on a clear bot signal, then **Upload to Decipher** (new survey, the survey uploaded last time, or replace the XML of a given survey path) or download the tracked file. Shows what was added, warnings (including "Decipher will refuse this file: ..."), and Decipher's own error messages in full. The upload panel only appears when the service has a Decipher API key.
- **Integrations:** Qualtrics and Decipher webhook addresses and configuration status, the API base URL, and setup notes.
- **Settings:** shows each editable setting (Decipher API key, base and company, Qualtrics token, OpenAI key and model, tracker API address, tracking token secret, detection threshold) and whether it comes from a saved value or the environment. Secrets only show set or not set. Editing needs an **admin unlock**: enter the admin token (the backend's `ADMIN_TOKEN`), which is kept in the browser's session storage for that tab and sent as `X-Admin-Token`. Without `ADMIN_TOKEN` on the backend the page is read-only. Saved values can be removed to fall back to the environment.
- **Quick start** and **API playground:** integration steps and an interactive API tester for developers.

### Shared UI kit
`src/components/ui/index.jsx` holds the shared building blocks, so pages look and behave the same:
- Layout: `PageHeader`, `Card`, `StatCard`
- Controls: `Button`, `buttonClass`, `inputClass`, `tableClasses`
- Status: `Badge`, `VerdictBadge`, `RiskBadge`, `RateBar`
- States: `EmptyState`, `Loading`, `ErrorBanner`
- Helpers: `apiError` (readable message from an API error), `toDate`, `timeAgo`, `formatDateTime`, `percent`

---

## Core Dependencies

### React & Core Libraries
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.20.1"
}
```

**Purpose:**
- **React 18**: Modern React with concurrent features and hooks
- **React DOM**: DOM rendering for React
- **React Router**: Client-side navigation (`HashRouter` in production, `BrowserRouter` locally)

### UI & Styling
```json
{
  "tailwindcss": "^3.3.6",
  "autoprefixer": "^10.4.16",
  "postcss": "^8.4.32",
  "clsx": "^2.0.0",
  "lucide-react": "^0.525.0"
}
```

**Purpose:**
- **Tailwind CSS**: Utility-first CSS framework
- **Autoprefixer**: Automatic vendor prefixes
- **PostCSS**: CSS processing pipeline
- **clsx**: Conditional className utility
- **Lucide React**: Icon library

### Data Visualization & Charts
```json
{
  "recharts": "^2.8.0"
}
```

**Purpose:**
- **Recharts**: React charting library for data visualization

### HTTP Client & Utilities
```json
{
  "axios": "^1.6.2",
  "date-fns": "^2.30.0"
}
```

**Purpose:**
- **Axios**: HTTP client for API communication
- **date-fns**: Date utility library

### User Feedback
```json
{
  "react-toastify": "^11.0.5"
}
```

**Purpose:**
- **React Toastify**: Toast notifications (bottom right)

---

## Development Dependencies

### Build Tools
```json
{
  "vite": "^5.0.0",
  "@vitejs/plugin-react": "^4.1.1"
}
```

**Purpose:**
- **Vite**: Fast build tool and dev server
- **@vitejs/plugin-react**: React support for Vite

### TypeScript Support
```json
{
  "@types/react": "^18.2.37",
  "@types/react-dom": "^18.2.15"
}
```

**Purpose:**
- Type definitions for React and React DOM

### Testing
```json
{
  "vitest": "^1.0.0",
  "@vitest/ui": "^1.0.0"
}
```

**Purpose:**
- **Vitest**: Unit testing framework
- **@vitest/ui**: Testing UI interface

### Code Quality
```json
{
  "eslint": "^8.53.0",
  "eslint-plugin-react": "^7.33.2",
  "eslint-plugin-react-hooks": "^4.6.0",
  "eslint-plugin-react-refresh": "^0.4.4"
}
```

**Purpose:**
- **ESLint**: JavaScript linting
- **eslint-plugin-react**: React-specific linting rules
- **eslint-plugin-react-hooks**: Hooks linting rules
- **eslint-plugin-react-refresh**: Fast refresh support

---

## Project Structure

```
frontend/
├── index.html                 # HTML entry point
├── src/
│   ├── App.jsx                # Routes and router choice (hash or normal paths)
│   ├── main.jsx               # App entry point
│   ├── config/
│   │   └── config.ts          # API and frontend base URLs, derived URLs
│   ├── services/
│   │   └── apiService.js      # API calls (sessions, dashboard, tracking, settings, live quality, ...)
│   ├── styles/
│   │   ├── App.css
│   │   └── index.css
│   └── components/
│       ├── layout/
│       │   └── AppShell.jsx   # Sidebar, phone top bar and menu, service status
│       ├── ui/
│       │   └── index.jsx      # Shared UI kit
│       ├── quality/           # Live Quality parts: rules, data file, shared pieces
│       ├── Overview.jsx
│       ├── LiveQuality.jsx
│       ├── SessionList.jsx
│       ├── SessionTable.jsx
│       ├── SessionDetails.jsx
│       ├── SurveyDetails.jsx
│       ├── PlatformDetails.jsx
│       ├── RespondentDetails.jsx
│       ├── HierarchicalNavigation.jsx
│       ├── TextAnalysis.jsx
│       ├── ReportBuilder.jsx
│       ├── SurveyTracking.jsx  # Add tracking page
│       ├── Integrations.jsx
│       ├── Settings.jsx
│       ├── QuickStartGuide.jsx
│       ├── ApiPlayground.jsx
│       └── *Widget.jsx, PerQuestionTimingTable.jsx  # Text, fraud, grid and timing panels
├── .env.example               # Local settings
├── .env.production            # Production settings (hash routing)
├── Dockerfile                 # Optional nginx image
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

---

## Configuration Files

### Vite Configuration (vite.config.js)
```javascript
export default defineConfig({
  plugins: [react()],
  base: process.env.NODE_ENV === 'production' ? './' : '/',
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true, secure: false }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['lucide-react', 'react-toastify'],
          charts: ['recharts']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  test: { globals: true, environment: 'jsdom', setupFiles: './src/test/setup.js' }
})
```

**Configuration Details:**
- **Base**: relative asset paths (`./`) in production, so the build works from the bucket's `index.html`
- **Port**: Development server runs on port 3000
- **Proxy**: Routes `/api` requests to the backend (localhost:8000)
- **Build**: Outputs to `dist` with source maps and separate vendor, router, ui and charts chunks

### Tailwind Configuration (tailwind.config.js)
- **Content**: Scans `index.html` and `src/**/*.{js,ts,jsx,tsx}` for classes
- **Font**: Inter, then system-ui
- **Colors**: A `primary` blue palette (50 to 900)

### PostCSS Configuration (postcss.config.js)
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

---

## Installation & Setup

### Prerequisites
- **Node.js**: Version 18 or higher (the Dockerfile uses Node 20)
- **npm**: Version 9 or higher
- **Git**: For version control

### Installation Steps

1. **Go to the frontend folder**
   ```bash
   cd bot_detection_live/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create the environment file**
   ```bash
   cp .env.example .env
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

### Environment Variables

| Variable | Used for | Local (`.env.example`) | Production (`.env.production`) |
|----------|----------|------------------------|--------------------------------|
| `VITE_API_BASE_URL` | Backend API base | `http://localhost:8000/api/v1` | `https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1` |
| `VITE_APP_NAME` | App name | `Bot Detection Dashboard` | `Bot Detection Dashboard` |
| `VITE_FRONTEND_BASE_URL` | Links to the dashboard itself | (not set) | `https://storage.googleapis.com/bot-detection-frontend-20251208` |
| `VITE_ROUTER_MODE` | `hash` for `index.html#/...` addresses | (not set: normal paths) | `hash` |

When a variable is missing, `src/config/config.ts` falls back to the production API and bucket addresses.

---

## Development Workflow

### Available Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui"
  }
}
```

### Development Best Practices

1. **Components**
   - Functional components with hooks
   - Build pages from the shared UI kit (`components/ui`) rather than one-off styles
   - Add new pages to `App.jsx` and, if they belong in the menu, to `NAV_GROUPS` in `AppShell.jsx`

2. **Data**
   - All API calls go through `services/apiService.js`
   - Show loading, empty and error states (`Loading`, `EmptyState`, `ErrorBanner`)
   - Show only real data; no placeholder figures or simulated results

3. **Styling**
   - Tailwind CSS classes
   - Check pages at phone width as well as desktop

---

## Build & Deployment

### Production Build

```bash
npx vite build --mode production
```

This reads `.env.production` (production API address and `VITE_ROUTER_MODE=hash`) and writes `dist/`.

### Deploying to the bucket (how production is done)

```bash
gcloud storage rsync -r frontend/dist gs://bot-detection-frontend-20251208
```

Then set cache headers: `index.html` as `no-cache`, and `assets/**` as `public, max-age=31536000, immutable`. Do not delete unmatched files in the bucket: `tracking-client.js` there may still be used by live surveys.

The dashboard is then at `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html`, with pages at `index.html#/<route>`.

### Docker (optional)

`frontend/Dockerfile` builds the app and serves it with nginx on port 3000, sending every path to `index.html`, so normal paths work there without `VITE_ROUTER_MODE=hash`.

---

## Testing

Vitest is installed and configured in `vite.config.js` (jsdom environment, setup file `./src/test/setup.js`), but the frontend has no test files yet, and `src/test/setup.js`, jsdom and Testing Library are not present. Add them before writing component tests.

```bash
npm test
npm run test:ui
```

---

## Code Quality

`npm run lint` runs ESLint with the React plugins listed above. There is no ESLint configuration file in the frontend folder yet, so add one (for example `.eslintrc.cjs` with `plugin:react-hooks/recommended`) before relying on the lint script.

---

## Browser Support

- **Chrome**: Version 90+
- **Firefox**: Version 88+
- **Safari**: Version 14+
- **Edge**: Version 90+

The layout works from phone width up (slide-out menu below the `lg` breakpoint).

---

## Performance Features

- **Chunking**: vendor, router, ui and charts code are split into separate chunks
- **Caching**: hashed files under `assets/` are cached for a year; `index.html` is not cached, so a new deploy shows at once
- **Polling**: the service status in the sidebar checks `/health` once a minute

---

## Troubleshooting

1. **Port Already in Use**
   ```bash
   npx kill-port 3000
   # Or change the port in vite.config.js
   ```

2. **Dependency Issues**
   ```bash
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **API Connection Issues**
   - Check the backend is running on port 8000
   - Check the proxy in `vite.config.js` and `VITE_API_BASE_URL`

4. **Production page is blank or a reload shows "not found"**
   - Use the hash address (`index.html#/quality`, not `/quality`)
   - Make sure the build used `--mode production`, so `VITE_ROUTER_MODE=hash` was set

5. **Settings cannot be saved**
   - Unlock with the admin token; a wrong token is refused (401)
   - If the backend has no `ADMIN_TOKEN`, Settings is read-only (403)

6. **No "Upload to Decipher" on Add tracking**
   - Save a Decipher API key on Settings (or set `DECIPHER_API_KEY` on the backend)

---

## Additional Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [React Router Documentation](https://reactrouter.com/)
