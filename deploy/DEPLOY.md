# Put Nexus Sight online (Hugging Face Spaces, free)

One container serves the website and the API. The result is a public link like
`https://huggingface.co/spaces/<your-hf-username>/nexus-sight`.
Files in this folder: `Dockerfile`, `serve.py` (website + API on one URL), `build_space.py`
(packs the app), `space_README.md` (the Space's page). No app code was changed.

## First time (about 15 minutes)

1. **Create the Space.** Sign in at huggingface.co → **New Space**:
   name `nexus-sight`, SDK **Docker** → **Blank**, hardware **CPU basic (free)**, **Public**.
2. **Pack the app.** In PowerShell, from `D:\C_analyzer\LOL-game-analyzer`:
   ```
   python deploy\build_space.py
   ```
   This creates `D:\C_analyzer\nexus-sight-space` (~120 MB). No `.env`, datasets or tests are included.
3. **Log in once.** Create a token with **Write** access at huggingface.co/settings/tokens, then:
   ```
   pip install -U huggingface_hub
   hf auth login
   ```
   Paste the token when asked. Don't put the token in any file or chat.
4. **Upload.**
   ```
   hf upload <your-hf-username>/nexus-sight D:\C_analyzer\nexus-sight-space . --repo-type space
   ```
   The 100 MB database uploads automatically as a large file.
5. **Wait for the build** (~5 minutes; watch the **Logs** tab on the Space). Then open the **App** tab.
   Direct link without the Hugging Face frame: `https://<your-hf-username>-nexus-sight.hf.space`

## After retraining or code changes

Run steps 2 and 4 again. The Space rebuilds itself.

## Good to know

- Free Spaces go to sleep after a long time with no visitors; the first visit then takes about a minute to wake up.
- The site is public, so keep secrets out of the repo. The app needs no API keys.
- Tested: website, `/api/teams`, `/api/team/{name}`, `/api/champion/...`, `/api/model` and `/api/predict`
  (Gen.G vs T1 full draft → 69% / 31% in 0.03 s) with Python 3.12 and the pinned `requirements.txt`.
