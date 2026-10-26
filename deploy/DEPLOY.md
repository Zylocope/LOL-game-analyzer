# Put Nexus Sight online (Render, free)

One Docker container serves the website and the API. Render's free web service builds it straight from the GitHub
repo. Free services sleep after 15 minutes without visitors; the next visit takes about a minute to wake them.
Memory use is about 215 MB (the free plan allows 512 MB).

> Hugging Face Spaces now require a paid PRO plan for Docker apps, so Render is the free option.

## First time

### 1. Push the latest code
```powershell
git add -A
git commit -m "Deploy setup for Render"
git push
```

### 2. Upload the database and model as a GitHub release (they are too big for Git)
1. Open https://github.com/Zylocope/LOL-game-analyzer/releases/new
2. **Choose a tag** → type `data-2026-10-26` → **Create new tag**.
3. Title: `Data and model (2026-10-26)`.
4. Drag in two files from `D:\C_analyzer\LOL-game-analyzer\backend\`: **`nexus_sight.db`** and **`model_v6.pkl`**.
   Wait until both finish uploading.
5. **Publish release**.

The Dockerfile downloads these two files from that release during the build (`DATA_URL` in `deploy/Dockerfile`).

### 3. Create the Render service
1. Sign up at https://render.com with your GitHub account.
2. **New → Web Service** → pick **Zylocope/LOL-game-analyzer**.
3. Settings:
   - **Language:** Docker
   - **Branch:** main
   - **Dockerfile Path:** `deploy/Dockerfile`
   - **Docker Build Context Directory:** `.` (the repo root)
   - **Instance Type:** Free
   - **Health Check Path** (under Advanced): `/healthz`
4. **Deploy Web Service**. The first build takes about 5–10 minutes; watch the **Logs**.
5. Your link: `https://<service-name>.onrender.com`. Open it, pick two teams and a draft, and check that a
   prediction appears.

## After new data or code changes

- **Code only:** push to `main`; Render rebuilds automatically.
- **New data:** import games, run `py -m backend.refresh_ratings`, upload the new `nexus_sight.db` and
  `model_v6.pkl` to a new release (e.g. `data-2027-01-15`), change `DATA_URL` in `deploy/Dockerfile` to that tag,
  then push.

## Good to know

- The app needs no API keys. Never add secrets to the repo or the release.
- Tested locally: website, `/api/teams`, `/api/team/{name}`, `/api/champions/recent`, `/api/model`, `/api/predict`.
- `deploy/build_space.py` still packs a folder for Hugging Face Spaces if you ever get PRO.
