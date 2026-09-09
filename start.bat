@echo off
echo ================================================
echo 🚀 Starting Edusphere Project...
echo ================================================

echo 🌐 Starting Backend...
start "Edusphere Backend" cmd /k "cd Edusphere_backend & if not exist .venv (python -m venv .venv) & call .venv\Scripts\activate & pip install -r requirements_simple.txt & python app.py"

echo 💻 Starting Frontend...
start "Edusphere Frontend" cmd /k "cd Edusphere_frontend & if not exist node_modules (npm install) & npm run dev"

echo ✅ Both servers are starting up in separate windows!
echo Backend will be at http://localhost:5001
echo Frontend will be at http://localhost:5173
echo ================================================
echo 🌐 Opening browser in 5 seconds...
timeout /t 5 >nul
start http://localhost:5173
