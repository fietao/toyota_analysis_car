# Run The Dashboard

From PowerShell:

```powershell
cd C:\dev\ai-reading-car-analysis\frontend
npm run dev -- --port 3001
```

On Windows, `RUN.bat` performs the same startup and opens the browser.

Open:

```text
http://localhost:3001
```

## Production Check

```powershell
cd C:\dev\ai-reading-car-analysis\frontend
npm run build
```

The production build is a static export in `frontend/out/` and is deployed by the
GitHub Pages workflow.

## Useful Checks

```powershell
npm run lint
npm run build
```
