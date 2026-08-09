# Socia. | Deployment & Production Guide

This guide provides step-by-step instructions for deploying Socia. to production environments.

## 🔗 Backend Deployment (Render / Railway)

### 1. Repository Setup
Ensure your GitHub repository contains both the `backend/` and `services/` directories, as the backend depends on the services for analysis.

### 2. Render Deployment
1. **New Web Service**: Connect your GitHub repository.
2. **Environment**: Select `Python`.
3. **Build Command**: `pip install -r backend/requirements.txt`
4. **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables**:
   - `OPENAI_API_KEY`: Your OpenAI API key.
   - `PYTHONPATH`: `/opt/render/project/src` (Ensure it includes the root to find `services`).

### 3. Railway Deployment
1. **New Project**: Deploy from GitHub repo.
2. **Settings**: Railway usually detects the root. If not, set the Root Directory to `/`.
3. **Variable**: `PORT` (Railway provides this), `OPENAI_API_KEY`.

---

## 🎨 Frontend Deployment (Netlify / Vercel)

### 1. Update API URL
Before deploying, update the `API_URL` in `frontend/app.js` to match your live backend URL (e.g., `https://socia-api.onrender.com`).

```javascript
// frontend/app.js
const API_URL = 'https://your-live-backend-api.com';
```

### 2. Netlify Deployment
1. **New Site**: Import from GitHub.
2. **Base Directory**: `frontend`
3. **Build Command**: (Leave empty)
4. **Publish Directory**: `.` (Relative to `frontend`)

### 3. Vercel Deployment
1. **New Project**: Select repository.
2. **Framework Preset**: Other.
3. **Root Directory**: `frontend`
4. **Output Directory**: `.`

---

## 🔑 Environment Variables Setup

| Variable | Description | Required |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | Your secret key from OpenAI Dashboard. | Yes |
| `API_URL` | The URL of your backend server (Frontend only). | Yes |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins (e.g. `https://my-site.netlify.app`). Defaults to localhost origins when unset. | No |
| `PORT` | The port the backend listens on (autoplaced by most hosts). | No |

---

## 🛡️ Production Checklist
- [ ] CORS is restricted to your production frontend domain (Update `allow_origins` in `main.py`).
- [ ] API keys are stored securely and NOT committed to version control.
- [ ] Error messages are user-friendly and do not leak sensitive system info.
- [ ] Health checks are active and monitored.
