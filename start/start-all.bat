start "server" cmd /k "cd /d C:\Users\benbu\language-tutor && uvicorn server:app --host 0.0.0.0 --port 8000"
start "ngrok" cmd /k "cd /d C:\Users\benbu\language-tutor && python start-ngrok.py"
start "expo" cmd /k "cd /d C:\Users\benbu\language-tutor\mobile && npx expo start --tunnel"
