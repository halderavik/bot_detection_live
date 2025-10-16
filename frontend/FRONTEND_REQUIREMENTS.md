# Frontend Requirements & Setup Guide

## Table of Contents
1. [Overview](#overview)
2. [Core Dependencies](#core-dependencies)
3. [Development Dependencies](#development-dependencies)
4. [Project Structure](#project-structure)
5. [Configuration Files](#configuration-files)
6. [Installation & Setup](#installation--setup)
7. [Development Workflow](#development-workflow)
8. [Build & Deployment](#build--deployment)
9. [Testing](#testing)
10. [Code Quality](#code-quality)
11. [Browser Support](#browser-support)
12. [Performance Features](#performance-features)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The Bot Detection Frontend is a React-based dashboard built with modern web technologies. It provides a comprehensive interface for monitoring bot detection sessions, managing integrations, and testing APIs.

### Key Features
- **Real-time Dashboard**: Live session monitoring and analysis results
- **Text Analysis Dashboard**: Real-time text quality analysis with filtering and pagination
- **Integration Management**: Webhook testing and status monitoring
- **API Playground**: Interactive API testing interface
- **Quick Start Guide**: Step-by-step integration instructions
- **Settings Interface**: System configuration management
- **Report Builder**: Enhanced reporting with text quality metrics integration
- **Toast Notifications**: User feedback and alerts
- **Responsive Design**: Mobile-friendly interface

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
- **React Router**: Client-side navigation and routing

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
- **Lucide React**: Modern icon library

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
- **date-fns**: Modern date utility library

### User Feedback
```json
{
  "react-toastify": "^11.0.5"
}
```

**Purpose:**
- **React Toastify**: Toast notification system

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
- **Vitest**: Fast unit testing framework
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
├── public/                    # Static assets
│   ├── favicon.ico           # Site favicon
│   └── index.html            # HTML entry point
├── src/
│   ├── components/           # React components
│   │   ├── Dashboard.jsx     # Main dashboard component
│   │   ├── Navigation.jsx    # Navigation component
│   │   ├── Integrations.jsx  # Integration management
│   │   ├── Settings.jsx      # System settings
│   │   ├── ApiPlayground.jsx # API testing interface
│   │   ├── QuickStartGuide.jsx # Getting started guide
│   │   ├── SessionDetails.jsx # Session analysis view
│   │   ├── SessionList.jsx   # Session list component
│   │   └── SessionTable.jsx  # Session table component
│   ├── services/             # API service layer
│   │   └── apiService.js     # API communication
│   ├── utils/                # Utility functions
│   │   └── formatters.js     # Data formatting utilities
│   ├── styles/               # CSS styles
│   │   ├── App.css           # Main app styles
│   │   └── index.css         # Global styles
│   ├── App.jsx               # Main app component
│   └── main.jsx              # App entry point
├── package.json              # Dependencies and scripts
├── package-lock.json         # Locked dependency versions
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # Tailwind configuration
├── postcss.config.js         # PostCSS configuration
├── .eslintrc.cjs             # ESLint configuration
├── .gitignore                # Git ignore rules
└── README.md                 # Project documentation
```

---

## Configuration Files

### Vite Configuration (vite.config.js)
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
  }
})
```

**Configuration Details:**
- **Port**: Development server runs on port 3000
- **Host**: Allows external access
- **Proxy**: Routes `/api` requests to backend (localhost:8000)
- **Build**: Outputs to `dist` directory with source maps
- **Test**: Uses jsdom environment for testing

### Tailwind Configuration (tailwind.config.js)
```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
    },
  },
  plugins: [],
}
```

**Configuration Details:**
- **Content**: Scans HTML and React files for classes
- **Font**: Uses Inter font family
- **Colors**: Custom primary color palette
- **Plugins**: Extensible plugin system

### PostCSS Configuration (postcss.config.js)
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

**Configuration Details:**
- **Tailwind CSS**: Processes Tailwind directives
- **Autoprefixer**: Adds vendor prefixes automatically

### ESLint Configuration (.eslintrc.cjs)
```javascript
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
  },
}
```

---

## Installation & Setup

### Prerequisites
- **Node.js**: Version 18 or higher
- **npm**: Version 9 or higher
- **Git**: For version control

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bot_iden_live/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create environment file**
   ```bash
   # Create .env file
   echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > .env
   echo "VITE_APP_NAME=Bot Detection Dashboard" >> .env
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

### Environment Variables

Create a `.env` file in the frontend directory:
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Application Configuration
VITE_APP_NAME=Bot Detection Dashboard

# Development Configuration
VITE_DEV_MODE=true
VITE_ENABLE_MOCK_DATA=false
```

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

### Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint

# Run tests
npm test

# Run tests with UI
npm run test:ui
```

### Development Best Practices

1. **Component Structure**
   - Use functional components with hooks
   - Keep components small and focused
   - Use proper prop types and validation

2. **State Management**
   - Use React hooks for local state
   - Use context for global state when needed
   - Avoid prop drilling

3. **Styling**
   - Use Tailwind CSS classes
   - Create reusable component classes
   - Follow responsive design principles

4. **API Integration**
   - Use the centralized apiService
   - Handle loading and error states
   - Implement proper error boundaries

---

## Build & Deployment

### Production Build

```bash
# Create production build
npm run build

# Preview production build locally
npm run preview
```

### Build Output

The build process creates a `dist` directory with:
- **HTML**: Entry point with optimized assets
- **CSS**: Minified and optimized styles
- **JavaScript**: Bundled and minified code
- **Assets**: Optimized images and other assets

### Deployment Options

1. **Static Hosting** (Netlify, Vercel, GitHub Pages)
   ```bash
   npm run build
   # Deploy dist/ directory
   ```

2. **Docker Deployment**
   ```dockerfile
   FROM node:18-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production
   COPY . .
   RUN npm run build
   FROM nginx:alpine
   COPY --from=0 /app/dist /usr/share/nginx/html
   ```

3. **CDN Deployment**
   - Upload `dist/` contents to CDN
   - Configure proper caching headers
   - Set up domain and SSL

---

## Testing

### Test Setup

```javascript
// src/test/setup.js
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import matchers from '@testing-library/jest-dom/matchers';

expect.extend(matchers);

afterEach(() => {
  cleanup();
});
```

### Test Structure

```
src/
├── components/
│   ├── __tests__/
│   │   ├── Dashboard.test.jsx
│   │   ├── Navigation.test.jsx
│   │   └── Integrations.test.jsx
│   └── Dashboard.jsx
└── services/
    ├── __tests__/
    │   └── apiService.test.js
    └── apiService.js
```

### Writing Tests

```javascript
// Example component test
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Dashboard from '../Dashboard';

describe('Dashboard', () => {
  it('renders dashboard title', () => {
    render(<Dashboard />);
    expect(screen.getByText('Bot Detection Dashboard')).toBeInTheDocument();
  });
});
```

### Test Commands

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm test -- --coverage
```

---

## Code Quality

### ESLint Rules

The project uses ESLint with React-specific rules:
- **React Hooks**: Enforces hooks rules
- **React Refresh**: Supports fast refresh
- **TypeScript**: Type checking (if using TypeScript)

### Code Formatting

```bash
# Format code with Prettier (if configured)
npx prettier --write src/

# Check formatting
npx prettier --check src/
```

### Pre-commit Hooks

Consider adding pre-commit hooks:
```json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged"
    }
  },
  "lint-staged": {
    "src/**/*.{js,jsx}": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

---

## Browser Support

### Supported Browsers

- **Chrome**: Version 90+
- **Firefox**: Version 88+
- **Safari**: Version 14+
- **Edge**: Version 90+

### Polyfills

The project uses modern JavaScript features. For older browsers, consider:
- **core-js**: For JavaScript polyfills
- **regenerator-runtime**: For async/await support

### CSS Support

- **CSS Grid**: Supported in all modern browsers
- **CSS Flexbox**: Widely supported
- **CSS Custom Properties**: Supported in modern browsers
- **Tailwind CSS**: Utility-first approach

---

## Performance Features

### Build Optimization

1. **Code Splitting**
   - Automatic route-based splitting
   - Dynamic imports for large components
   - Vendor chunk separation

2. **Tree Shaking**
   - Unused code elimination
   - Dead code removal
   - Optimized bundle size

3. **Asset Optimization**
   - Image compression
   - CSS minification
   - JavaScript minification

### Runtime Performance

1. **React Optimization**
   - React.memo for component memoization
   - useMemo for expensive calculations
   - useCallback for function memoization

2. **Bundle Analysis**
   ```bash
   # Analyze bundle size
   npm run build -- --analyze
   ```

3. **Performance Monitoring**
   - React DevTools Profiler
   - Lighthouse audits
   - Core Web Vitals monitoring

---

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill process on port 3000
   npx kill-port 3000
   # Or change port in vite.config.js
   ```

2. **Dependency Issues**
   ```bash
   # Clear npm cache
   npm cache clean --force
   # Remove node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Build Failures**
   ```bash
   # Check for linting errors
   npm run lint
   # Check for TypeScript errors (if using TS)
   npx tsc --noEmit
   ```

4. **API Connection Issues**
   - Verify backend is running on port 8000
   - Check proxy configuration in vite.config.js
   - Verify environment variables

### Debug Mode

Enable debug mode for development:
```javascript
// In vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      }
    }
  }
})
```

### Performance Issues

1. **Slow Development Server**
   - Check for large dependencies
   - Use Vite's dependency optimization
   - Consider using pnpm for faster installs

2. **Large Bundle Size**
   - Analyze bundle with `npm run build -- --analyze`
   - Implement code splitting
   - Remove unused dependencies

3. **Memory Issues**
   - Increase Node.js memory limit: `NODE_OPTIONS="--max-old-space-size=4096"`
   - Use production builds for testing

---

## Additional Resources

### Documentation
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [React Router Documentation](https://reactrouter.com/)

### Tools
- [React DevTools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
- [Vite DevTools](https://github.com/vitejs/vite-plugin-inspect)
- [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)

### Community
- [React Community](https://reactjs.org/community/support.html)
- [Vite Community](https://github.com/vitejs/vite/discussions)
- [Tailwind CSS Community](https://tailwindcss.com/community)

---

*Last updated: June 29, 2025* 