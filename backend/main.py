#!/usr/bin/env python3
"""
FastAPI Server Launcher
"""

import uvicorn
import os

def main():
    """Run the FastAPI application"""
    
    # Set environment variables if not already set
    if not os.getenv('JWT_SECRET_KEY'):
        os.environ['JWT_SECRET_KEY'] = 'your-secret-key-change-this'
    
    print("Starting LLM RAG Exam Grading API Server...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
