# start_dev.ps1 — starts backend
# Window 1: ngrok http 8000 --domain=tractably-extraembryonic-turner.ngrok-free.app
# Window 2: this script
# Window 3: cd mobile && npx expo start --tunnel

Set-Location $PSScriptRoot
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
