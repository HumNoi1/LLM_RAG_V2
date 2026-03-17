# 🚀 วิธีการเริ่มใช้งานระบบ Register

## ขั้นตอนที่ 1: เตรียมสภาพแวดล้อม

```bash
# เข้าไปใน backend directory
cd backend

# ติดตั้ง dependencies (ถ้ายังไม่ได้ติดตั้ง)
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] psycopg2-binary

# หรือติดตั้งจาก requirements.txt
pip install -r requirements.txt
```

## ขั้นตอนที่ 2: เริ่มต้น Server

### วิธีที่ 1: ใช้ main.py
```bash
python main.py
```

### วิธีที่ 2: ใช้ uvicorn โดยตรง
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## ขั้นตอนที่ 3: เข้าใช้งาน

เมื่อ server เริ่มต้นแล้ว จะสามารถเข้าใช้งานได้ที่:

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs  ← **ใช้ทดสอบ API ได้เลย!**
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## ขั้นตอนที่ 4: ทดสอบ API Endpoints

### 1. เปิด Swagger UI
ไปที่: http://localhost:8000/docs

### 2. ทดสอบ Register (สมัครสมาชิก)
```
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "role": "teacher"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com", 
  "full_name": "John Doe",
  "role": "teacher",
  "created_at": "2024-03-17T10:30:00Z"
}
```

### 3. ทดสอบ Login (เข้าสู่ระบบ)
```
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 4. ทดสอบ Profile (ดูข้อมูลตัวเอง)
```
GET /api/v1/auth/me
```

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```

## ขั้นตอนที่ 5: ทดสอบด้วย curl (ถ้าต้องการ)

### Register
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpassword123",
       "full_name": "Test User",
       "role": "teacher"
     }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpassword123"
     }'
```

## 🔧 แก้ปัญหาที่อาจพบ

### ปัญหา: ModuleNotFoundError
```bash
pip install fastapi uvicorn
```

### ปัญหา: Database connection
ตรวจสอบไฟล์ `.env` ว่ามี `DATABASE_URL` ที่ถูกต้อง

### ปัญหา: JWT Secret Key
ตรวจสอบไฟล์ `.env` ว่ามี `JWT_SECRET_KEY`

## 📝 สรุป

1. **ง่ายที่สุด**: เปิด http://localhost:8000/docs และทดสอบผ่าน Swagger UI
2. **Command Line**: ใช้ curl commands ด้านบน
3. **Postman**: Import endpoints จาก http://localhost:8000/openapi.json

ระบบ register พร้อมใช้งานแล้ว! 🎉