"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { BookOpen, Mail, Lock, User, CheckCircle2, AlertCircle, BadgeCheck, Eye, EyeOff } from 'lucide-react';
import api from '@/lib/api';

type FormMode = 'login' | 'register';

export default function App() {
  const router = useRouter();
  const [mode, setMode] = useState<FormMode>('login');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const [formData, setFormData] = useState({
    name: '', teacherId: '', email: '', password: '', confirmPassword: ''
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Validation helper functions
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password: string): boolean => {
    return password.length >= 8;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    
    if (mode === 'register') {
      if (!formData.name || !formData.email || !formData.password) {
        setMessage({ type: 'error', text: 'กรุณากรอกข้อมูลให้ครบถ้วน' });
        return;
      }
      if (!validateEmail(formData.email)) {
        setMessage({ type: 'error', text: 'อีเมลไม่ถูกต้อง' });
        return;
      }
      if (!validatePassword(formData.password)) {
        setMessage({ type: 'error', text: 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร' });
        return;
      }
      if (formData.password !== formData.confirmPassword) {
        setMessage({ type: 'error', text: 'รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน' });
        return;
      }
      
      try {
        const registerRes = await api.post('/auth/register', {
          email: formData.email,
          password: formData.password,
          full_name: formData.name,
          role: 'teacher',
        });

        // Auto-login after registration
        const loginRes = await api.post('/auth/login', {
          email: formData.email,
          password: formData.password,
        });

        const { access_token, refresh_token } = loginRes.data;
        localStorage.setItem('authToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);
        localStorage.setItem('user', JSON.stringify(registerRes.data));

        setMessage({ type: 'success', text: 'ลงทะเบียนสำเร็จ! และเข้าสู่ระบบแล้ว' });
        setTimeout(() => {
          router.push('/dashboard');
        }, 800);
      } catch (err: any) {
        const detail = err?.response?.data?.detail || 'เกิดข้อผิดพลาดในการลงทะเบียน';
        setMessage({ type: 'error', text: detail });
      }
    } else {
      if (!formData.email || !formData.password) {
        setMessage({ type: 'error', text: 'กรุณากรอกอีเมลและรหัสผ่าน' });
        return;
      }
      if (!validateEmail(formData.email)) {
        setMessage({ type: 'error', text: 'อีเมลไม่ถูกต้อง' });
        return;
      }

      try {
        const loginRes = await api.post('/auth/login', {
          email: formData.email,
          password: formData.password,
        });

        const { access_token, refresh_token } = loginRes.data;
        localStorage.setItem('authToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);

        // Fetch user profile
        const meRes = await api.get('/auth/me', {
          headers: { Authorization: `Bearer ${access_token}` },
        });
        localStorage.setItem('user', JSON.stringify(meRes.data));

        setMessage({ type: 'success', text: 'เข้าสู่ระบบสำเร็จ ยินดีต้อนรับอาจารย์' });
        setTimeout(() => {
          router.push('/dashboard');
        }, 800);
      } catch (err: any) {
        const detail = err?.response?.data?.detail || 'อีเมลหรือรหัสผ่านไม่ถูกต้อง';
        setMessage({ type: 'error', text: detail });
      }
    }
  };

  const switchMode = (next: FormMode) => {
    setMode(next);
    setMessage(null);
    setFormData({ name: '', teacherId: '', email: '', password: '', confirmPassword: '' });
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          font-family: 'Sarabun', sans-serif;
          background: #f0f4ff;
          min-height: 100vh;
        }

        .page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px;
          background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 50%, #ede9fe 100%);
          position: relative;
          overflow: hidden;
        }

        /* Decorative blobs */
        .blob {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          opacity: 0.35;
          pointer-events: none;
        }
        .blob-1 { width: 400px; height: 400px; background: #818cf8; top: -120px; left: -120px; }
        .blob-2 { width: 300px; height: 300px; background: #a78bfa; bottom: -80px; right: -80px; }
        .blob-3 { width: 200px; height: 200px; background: #6366f1; top: 40%; left: 60%; }

        /* Card */
        .card {
          width: 100%;
          max-width: 420px;
          background: rgba(255,255,255,0.85);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-radius: 24px;
          border: 1px solid rgba(255,255,255,0.9);
          box-shadow: 0 20px 60px rgba(99,102,241,0.15), 0 4px 20px rgba(0,0,0,0.06);
          overflow: hidden;
          position: relative;
          z-index: 1;
        }

        /* Header */
        .card-header {
          background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
          padding: 36px 32px 32px;
          text-align: center;
          position: relative;
          overflow: hidden;
        }
        .card-header::before {
          content: '';
          position: absolute;
          top: -40px; right: -40px;
          width: 160px; height: 160px;
          border-radius: 50%;
          background: rgba(255,255,255,0.07);
        }
        .card-header::after {
          content: '';
          position: absolute;
          bottom: -30px; left: -30px;
          width: 120px; height: 120px;
          border-radius: 50%;
          background: rgba(255,255,255,0.05);
        }

        .icon-wrap {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 64px; height: 64px;
          background: rgba(255,255,255,0.2);
          border-radius: 20px;
          margin-bottom: 16px;
          border: 1px solid rgba(255,255,255,0.25);
          position: relative; z-index: 1;
        }

        .card-title {
          color: #fff;
          font-size: 22px;
          font-weight: 700;
          letter-spacing: -0.3px;
          position: relative; z-index: 1;
        }
        .card-subtitle {
          color: rgba(255,255,255,0.75);
          font-size: 13px;
          margin-top: 4px;
          position: relative; z-index: 1;
        }

        /* Body */
        .card-body { padding: 28px 32px 32px; }

        /* Tabs */
        .tabs {
          display: flex;
          background: #f1f5f9;
          border-radius: 12px;
          padding: 4px;
          margin-bottom: 24px;
          gap: 4px;
        }
        .tab-btn {
          flex: 1;
          padding: 9px 0;
          border: none;
          background: transparent;
          border-radius: 9px;
          font-family: 'Sarabun', sans-serif;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          color: #94a3b8;
        }
        .tab-btn.active {
          background: #fff;
          color: #4f46e5;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        /* Alert */
        .alert {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 12px 14px;
          border-radius: 10px;
          font-size: 13px;
          margin-bottom: 20px;
          line-height: 1.5;
        }
        .alert.success { background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }
        .alert.error   { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
        .alert svg { flex-shrink: 0; margin-top: 1px; }

        /* Form */
        .form { display: flex; flex-direction: column; gap: 14px; }

        .field { position: relative; }
        .field-icon {
          position: absolute;
          left: 13px; top: 50%;
          transform: translateY(-50%);
          color: #a0aec0;
          display: flex;
          pointer-events: none;
        }
        .field-icon-right {
          position: absolute;
          right: 13px; top: 50%;
          transform: translateY(-50%);
          color: #a0aec0;
          display: flex;
          cursor: pointer;
          background: none;
          border: none;
          padding: 0;
        }
        .field-icon-right:hover { color: #4f46e5; }

        input[type="text"],
        input[type="email"],
        input[type="password"] {
          width: 100%;
          padding: 11px 14px 11px 40px;
          border: 1.5px solid #e2e8f0;
          border-radius: 10px;
          font-family: 'Sarabun', sans-serif;
          font-size: 14px;
          color: #1e293b;
          background: #fff;
          transition: border-color 0.2s, box-shadow 0.2s;
          outline: none;
        }
        input:focus {
          border-color: #6366f1;
          box-shadow: 0 0 0 3px rgba(99,102,241,0.12);
        }
        input::placeholder { color: #c4cdd6; }

        input[type="password"] { padding-right: 42px; }

        /* Row: remember + forgot */
        .row-between {
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 13px;
        }
        .remember {
          display: flex;
          align-items: center;
          gap: 7px;
          color: #64748b;
          cursor: pointer;
        }
        input[type="checkbox"] {
          width: 15px; height: 15px;
          accent-color: #4f46e5;
          cursor: pointer;
        }
        .forgot { color: #4f46e5; font-weight: 600; text-decoration: none; font-size: 13px; }
        .forgot:hover { text-decoration: underline; }

        /* Submit button */
        .btn-submit {
          width: 100%;
          padding: 13px;
          border: none;
          border-radius: 12px;
          background: linear-gradient(135deg, #4f46e5, #7c3aed);
          color: #fff;
          font-family: 'Sarabun', sans-serif;
          font-size: 15px;
          font-weight: 700;
          cursor: pointer;
          transition: opacity 0.2s, transform 0.1s, box-shadow 0.2s;
          box-shadow: 0 4px 14px rgba(99,102,241,0.35);
          margin-top: 4px;
          letter-spacing: 0.2px;
        }
        .btn-submit:hover { opacity: 0.92; box-shadow: 0 6px 20px rgba(99,102,241,0.45); }
        .btn-submit:active { transform: scale(0.98); }

        /* Footer */
        .card-footer {
          text-align: center;
          margin-top: 24px;
          font-size: 13px;
          color: #94a3b8;
        }
        .card-footer button {
          background: none; border: none;
          color: #4f46e5; font-weight: 700;
          font-family: 'Sarabun', sans-serif;
          font-size: 13px; cursor: pointer;
        }
        .card-footer button:hover { text-decoration: underline; }
        .copyright { margin-top: 12px; font-size: 11px; color: #cbd5e1; }

        /* Badge */
        .badge {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          background: rgba(99,102,241,0.08);
          color: #4f46e5;
          font-size: 11px;
          font-weight: 600;
          padding: 3px 10px;
          border-radius: 20px;
          border: 1px solid rgba(99,102,241,0.2);
          margin-bottom: 20px;
        }
      `}</style>

      <div className="page">
        <div className="blob blob-1" />
        <div className="blob blob-2" />
        <div className="blob blob-3" />

        <div className="card">
          {/* Header */}
          <div className="card-header">
            <div className="icon-wrap">
              <BookOpen size={30} color="#fff" />
            </div>
            <h1 className="card-title">Teacher Portal</h1>
            <p className="card-subtitle">ระบบจัดการข้อมูลสำหรับคณาจารย์</p>
          </div>

          {/* Body */}
          <div className="card-body">

            {/* Tabs */}
            <div className="tabs">
              <button className={`tab-btn ${mode === 'login' ? 'active' : ''}`} onClick={() => switchMode('login')}>
                เข้าสู่ระบบ
              </button>
              <button className={`tab-btn ${mode === 'register' ? 'active' : ''}`} onClick={() => switchMode('register')}>
                ลงทะเบียน
              </button>
            </div>

            {/* Alert */}
            {message && (
              <div className={`alert ${message.type}`}>
                {message.type === 'success'
                  ? <CheckCircle2 size={16} />
                  : <AlertCircle size={16} />
                }
                <span>{message.text}</span>
              </div>
            )}

            {/* Form */}
            <form className="form" onSubmit={handleSubmit}>

              {mode === 'register' && (
                <>
                  <div className="field">
                    <span className="field-icon"><User size={16} /></span>
                    <input type="text" name="name" value={formData.name} onChange={handleInputChange} placeholder="ชื่อ - นามสกุล" />
                  </div>
                  <div className="field">
                    <span className="field-icon"><BadgeCheck size={16} /></span>
                    <input type="text" name="teacherId" value={formData.teacherId} onChange={handleInputChange} placeholder="รหัสประจำตัวอาจารย์" />
                  </div>
                </>
              )}

              <div className="field">
                <span className="field-icon"><Mail size={16} /></span>
                <input type="email" name="email" value={formData.email} onChange={handleInputChange} placeholder="อีเมลสถาบัน (name@university.ac.th)" />
              </div>

              <div className="field">
                <span className="field-icon"><Lock size={16} /></span>
                <input type={showPassword ? 'text' : 'password'} name="password" value={formData.password} onChange={handleInputChange} placeholder="รหัสผ่าน" />
                <button type="button" className="field-icon-right" onClick={() => setShowPassword(p => !p)}>
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>

              {mode === 'register' && (
                <div className="field">
                  <span className="field-icon"><Lock size={16} /></span>
                  <input type={showConfirm ? 'text' : 'password'} name="confirmPassword" value={formData.confirmPassword} onChange={handleInputChange} placeholder="ยืนยันรหัสผ่านอีกครั้ง" />
                  <button type="button" className="field-icon-right" onClick={() => setShowConfirm(p => !p)}>
                    {showConfirm ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              )}

              {mode === 'login' && (
                <div className="row-between">
                  <label className="remember">
                    <input type="checkbox" />
                    จดจำฉันไว้ในระบบ
                  </label>
                  <a href="#" className="forgot">ลืมรหัสผ่าน?</a>
                </div>
              )}

              <button type="submit" className="btn-submit">
                {mode === 'login' ? 'เข้าสู่ระบบ' : 'ลงทะเบียน'}
              </button>
            </form>

            {/* Footer */}
            <div className="card-footer">
              {mode === 'login' ? (
                <p>ยังไม่มีบัญชี? <button onClick={() => switchMode('register')}>ลงทะเบียนที่นี่</button></p>
              ) : (
                <p>มีบัญชีอยู่แล้ว? <button onClick={() => switchMode('login')}>เข้าสู่ระบบ</button></p>
              )}
              <p className="copyright">© {new Date().getFullYear()} University Name. All rights reserved.</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}