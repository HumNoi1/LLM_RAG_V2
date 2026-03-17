@echo off

echo ===============================================
echo Starting LLM RAG Exam Grading API Server
echo ===============================================
echo.
echo Server: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Health: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo ===============================================

cd backend

REM Set environment variables
set JWT_SECRET_KEY=your-secret-key-change-this
set DATABASE_URL=postgresql://postgres.urdgwffjkfsibfkenifx:LyqWEDSByP3bB0LB@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true

REM Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload