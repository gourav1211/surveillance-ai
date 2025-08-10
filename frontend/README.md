# Surveillance AI Dashboard

A modern React dashboard for AI-powered surveillance monitoring with real-time video streams, analytics, and alert management.

## Features

- 🎥 **Live Video Streaming** - HLS video player with real-time feed
- 📊 **Analytics Dashboard** - Real-time statistics and trend visualization  
- 🚨 **Alert Management** - Live alerts with severity levels, GPS coordinates, and detailed information
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile devices
- 🌙 **Dark Theme** - Professional dark interface optimized for monitoring

## Technology Stack

- **Frontend**: React 19 + Vite
- **Styling**: Tailwind CSS v4
- **Charts**: Recharts
- **Video**: HLS.js for live streaming
- **HTTP Client**: Axios
- **Date Handling**: date-fns

## Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Configure backend API** (optional)
   
   Create `.env.local` file:
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   ```
   http://localhost:5173
   ```

### Build for Production

```bash
npm run build
npm run preview  # Preview production build
```

## API Integration

The dashboard expects the following backend endpoints:

### Stream Information
```
GET /api/stream
Response: { "url": "https://example.com/stream.m3u8" }
```

### Analytics Summary  
```
GET /api/analytics/summary
Response: {
  "total": 42,
  "critical": 3, 
  "high": 8,
  "blackout": 1,
  "trend": [
    { "time": "2025-01-01T00:00:00Z", "count": 5 }
  ]
}
```

### Alerts List
```
GET /api/alerts?limit=20
Response: [
  {
    "id": 1,
    "timestamp": "2025-01-01T00:00:00Z",
    "title": "Motion Detected",
    "reason": "Unauthorized access",
    "severity": "critical", // critical, high, medium, low
    "location": "Warehouse A",
    "lat": 40.7128,
    "lng": -74.0060,
    "details": "Additional information...",
    "detections": { "objects": ["person"], "confidence": 0.94 }
  }
]
```

### Live Alert Stream (Server-Sent Events)
```
GET /api/alerts/stream
Event data: Same format as alerts list items
```+ Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
