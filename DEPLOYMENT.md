# Multi-Environment Configuration Guide

This project is configured to work seamlessly in both **development** and **production** environments without code changes.

## 📋 Environment Setup

### Frontend (Next.js)

The frontend uses Next.js environment variables for API configuration:

- **Development**: Uses `.env.local` 
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```
  
- **Production**: Uses `.env.production`
  ```
  NEXT_PUBLIC_API_URL=https://site-cni.onrender.com
  ```

Next.js automatically selects the correct environment file based on the build context:
- `npm run dev` → uses `.env.local`
- `npm run build` → uses `.env.production`

### Backend (FastAPI)

The backend uses environment variables for CORS configuration:

- **Development** (`.env`):
  ```
  CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.100.10:3000,https://sadp-2ixkl262q-ayoub-ben-hamadas-projects.vercel.app,https://site-cni.onrender.com
  ```

- **Production** (`.env.production`):
  ```
  CORS_ORIGINS=https://sadp-2ixkl262q-ayoub-ben-hamadas-projects.vercel.app,https://site-cni.onrender.com
  ```

## 🚀 Deployment Instructions

### Local Development

1. **Backend** - Already configured in `.env`:
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload
   ```
   Backend runs at `http://localhost:8000`

2. **Frontend** - Uses `.env.local`:
   ```bash
   cd frontend
   npm install  # or pnpm install
   npm run dev
   ```
   Frontend runs at `http://localhost:3000`

### Production Deployment

#### Backend (Render.com or similar)

1. Set environment variables in your hosting platform:
   ```
   DATABASE_URL=your-production-database-url
   JWT_SECRET=your-production-jwt-secret
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://site-cni.onrender.com
   ```

  The backend does not rely on a committed `.env` file in production. On Render, `DATABASE_URL` must be configured in the service environment or attached PostgreSQL resource.

2. Deploy the backend from the `backend/` directory
3. Use this start command on Render, or let Render pick it up from `backend/Procfile`:
   ```bash
   gunicorn -b 0.0.0.0:$PORT main:app -k uvicorn.workers.UvicornWorker
   ```

   This is the critical part for Render: the service must bind to `0.0.0.0` and the platform-provided `$PORT`, otherwise the port scanner will report no open ports.

#### Frontend (Vercel)

1. Connect your repository to Vercel
2. Set build settings:
   - **Framework**: Next.js
   - **Build Command**: `npm run build` (or `pnpm build`)
   - **Output Directory**: `.next`
   - **Root Directory**: `frontend`

3. Set environment variables in Vercel dashboard:
   ```
  NEXT_PUBLIC_API_URL=https://your-backend-domain.onrender.com
   ```

Vercel automatically uses `.env.production` during builds.

## ✅ Configuration Checklist

- [x] Frontend `.env.local` created for development
- [x] Frontend `.env.production` created for production  
- [x] Backend CORS configuration uses `settings.cors_origins`
- [x] Backend `.env` includes all required origins
- [x] Backend `.env.example` created for reference
- [x] Backend `.env.production` created for production
- [x] All API calls in frontend use `NEXT_PUBLIC_API_URL` variable
- [x] No hardcoded localhost URLs in production code

## 🔧 How It Works

### Frontend API Configuration

All API calls in the frontend use the centralized `apiRequest` function from `lib/api.ts`:

```typescript
const API_BASE = 
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000"

export async function apiRequest<T>(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    // ... request handling
  })
  // ...
}
```

This ensures all requests automatically use the correct API base URL for the environment.

### Backend CORS Configuration

The backend reads CORS origins from the `.env` file at startup:

```python
@dataclass
class Settings:
    cors_origins: list[str] = field(
        default_factory=lambda: [s.strip() for s in os.getenv("CORS_ORIGINS", "*").split(",")]
    )
```

And applies them in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Automatically loaded from env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🐛 Troubleshooting

**Frontend can't reach backend?**
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify backend is running at the correct address
- Check browser console for CORS errors

**CORS errors in browser?**
- Verify frontend domain is in backend `CORS_ORIGINS`
- Ensure backend is using latest `.env` configuration
- Restart backend after changing environment variables

**Production API calls failing?**
- Verify `NEXT_PUBLIC_API_URL` is set in production build
- Check backend environment variables on production server
- Ensure firewall/security rules allow frontend→backend communication

