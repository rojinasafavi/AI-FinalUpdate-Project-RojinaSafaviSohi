# Socia. | AI-Powered Social Media Analytics

Socia. is a premium full-stack analytics platform built with a **FastAPI** backend and a **Vanilla JS** frontend. It leverages AI (Google Gemini via its OpenAI-compatible endpoint) to provide sentiment analysis, topic identification, and strategic management reporting from social media datasets.

![Dashboard Preview](https://via.placeholder.com/1200x600.png?text=Socia+Analytics+Dashboard+Preview)

## ✨ Key Features

- **Automated Sentiment Analysis**: Real-time breakdown of positive, neutral, and negative sentiment.
- **Topic Extraction**: Identification of common trends and discussions within your data.
- **Executive Reporting**: High-level management reports including risks, opportunities, and strategic insights.
- **Premium UI/UX**: Minimalist light theme with smooth transitions, responsive design, and status monitoring.
- **Robust API**: Asynchronous backend with CORS enabled and comprehensive error handling.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- Google Gemini API Key (free tier available at https://aistudio.google.com/apikey)

### 2. Backend Setup
1. **Navigate to backend**: `cd backend`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure Environment**: Create a `.env` file in the root with:
   ```env
   GEMINI_API_KEY=your_key_here
   ```
   Optional variables:
   ```env
   GEMINI_MODEL=gemini-flash-latest   # default: gemini-2.0-flash
   GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   ```
4. **Start Server**: `uvicorn main:app --reload`
   - Access API docs at: `http://localhost:8000/docs`

### 3. Verify Your API Key
Test your Gemini key with a quick request:
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent" \
  -H 'Content-Type: application/json' \
  -H 'X-goog-api-key: your_key_here' \
  -X POST \
  -d '{"contents": [{"parts": [{"text": "Explain how AI works in a few words"}]}]}'
```

### 4. Run the Analysis Pipeline / Dashboard
```bash
python main.py                  # CLI pipeline → reports/management_report.md
streamlit run dashboard.py      # interactive dashboard
```

### 5. Frontend Setup
1. **Navigate to frontend**: `cd frontend`
2. **Serve files**: Use any live server or Python:
   ```bash
   python -m http.server 3000
   ```
3. **Open browser**: `http://localhost:3000`

## 🛠️ Deployment

For production deployment, see our [Detailed Deployment Guide](DEPLOYMENT.md).

### Summary
- **Backend**: Deploy the `backend/` folder to **Render** or **Railway**. Set `GEMINI_API_KEY` in environment variables.
- **Frontend**: Deploy the `frontend/` folder to **Netlify** or **Vercel**. Update `API_URL` in `app.js` to point to your live backend.

## 🐳 Docker Support
Build and run the backend using Docker:
```bash
docker build -t socia-backend -f backend/Dockerfile .
docker run -p 8000:8000 --env-file .env socia-backend
```

---
© 2024 Socia Analytics. Built with ❤️ for Advanced Coding.
