ChronoAI backend fix

Files:
- app.py: corrected CORS matching for this ChronoAI Vercel project and production cookie defaults.
- requirements.txt: dependencies from the provided backend.
- Procfile: web: gunicorn app:app

Install:
1. Replace these files in the existing backend folder in your GitHub repository.
2. Do NOT register/import auth.py as a blueprint; app.py already defines /api/register, /api/login, /api/me, and /api/logout. auth.py uses a different password field and is redundant.
3. In Render, confirm Root Directory is backend (if the files live in backend/), and Start Command is `gunicorn app:app`.
4. Set these Render environment variables:
   FRONTEND_URL=https://chronoai-orcin.vercel.app
   PRODUCTION=true
   SECRET_KEY=<a new private random value>
   Keep your existing MONGO_URI and Upstash Redis environment variables.
5. Commit and push the changed backend files, then wait for Render to redeploy.
6. Check https://chronoai-7.onrender.com/api/health

Never put MONGO_URI, SECRET_KEY, or the Upstash token in frontend code or public chat.
