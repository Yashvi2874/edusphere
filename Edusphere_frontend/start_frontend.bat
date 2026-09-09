@echo off
echo 🚀 Starting Edusphere Frontend...
echo ================================================

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
)

echo 🌐 Starting development server on http://localhost:5173...
echo ================================================

REM Start the development server
npm run dev

pause

