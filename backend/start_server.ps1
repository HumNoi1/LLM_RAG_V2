Write-Host "==============================================="
Write-Host "🚀 Starting LLM RAG Exam Grading API Server" -ForegroundColor Green
Write-Host "==============================================="
Write-Host ""
Write-Host "📡 Server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan  
Write-Host "🔍 Health: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "==============================================="

# Set environment variables
$env:JWT_SECRET_KEY="your-secret-key-change-this"
$env:DATABASE_URL="postgresql://postgres.urdgwffjkfsibfkenifx:LyqWEDSByP3bB0LB@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true"

# Start the server
python main.py