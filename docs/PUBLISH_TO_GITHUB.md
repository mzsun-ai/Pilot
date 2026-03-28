# Publish Pilot to GitHub

## Security first

- **Never commit passwords or tokens** to the repository.
- Use a **Personal Access Token (PAT)** or **SSH key** to push. GitHub no longer accepts account passwords for `git push` over HTTPS for most accounts (especially Google sign-in).

## Create the repository on GitHub

1. Open [github.com/new](https://github.com/new).
2. Repository name: **`Pilot`** (or `pilot-em` if `Pilot` is taken).
3. Description (example):

   > **Pilot** — Natural-language electromagnetic design assistant: parses requests, plans openEMS FDTD jobs, runs **open-source openEMS** (or mock fallback), and serves a bilingual web UI. No commercial solvers.

4. Choose **Public**.
5. Do **not** add a README/license/gitignore on GitHub (this repo already has them).
6. Create the repository.

## Push from your machine

```bash
cd /home/mingze/Pilot

# If not already initialized:
git init
git add .
git commit -m "Initial release: openEMS agent, web UI, i18n"

git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/Pilot.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. When prompted for a password, use a **GitHub PAT** (Settings → Developer settings → Personal access tokens), not your Google password.

With SSH:

```bash
git remote add origin git@github.com:YOUR_USERNAME/Pilot.git
git push -u origin main
```

## Let others use the website

**GitHub Pages** only hosts **static** files. This project needs a **Python server** (FastAPI + uvicorn) for `/api/v1/simulations` and related routes (see `docs/API.md`).

Options:

1. **Docker** — Use the included `Dockerfile` and deploy to [Render](https://render.com), [Fly.io](https://fly.io), [Railway](https://railway.app), etc. (free tiers vary). The default image runs the UI; **openEMS will use mock mode** unless you build openEMS into the image (see `deps/BUILD.md`).

2. **Self-hosted** — Clone the repo, `conda`/`pip` install, run `uvicorn web.app:app --host 0.0.0.0 --port 8765`, put a reverse proxy in front.

3. **README link** — Point users to your deployed URL once you have one.
