"use client";

import React, { useState, useEffect } from 'react';
import {
  BookOpen, FileText, ClipboardList, LogOut, Bell,
  TrendingUp, Users, ChevronRight, Clock, CheckCircle, AlertCircle, LayoutDashboard
} from 'lucide-react';
import { ProtectedRoute } from '@/src/components/ProtectedRoute';

// ─── Mock Data ────────────────────────────────────────────────────────────────
const MOCK_STATS = {
  totalCourses: 6,
  totalExams: 24,
  totalQuestions: 318,
  activeStudents: 142,
};

const MOCK_RECENT_EXAMS = [
  { id: 1, title: 'Midterm: คณิตศาสตร์วิศวกรรม I', course: 'ENG2101', questions: 40, status: 'published', date: '12 มิ.ย. 2567' },
  { id: 2, title: 'Quiz 3: โครงสร้างข้อมูล', course: 'CS2203', questions: 15, status: 'draft', date: '10 มิ.ย. 2567' },
  { id: 3, title: 'Final: ฟิสิกส์ทั่วไป', course: 'SCI1101', questions: 60, status: 'published', date: '8 มิ.ย. 2567' },
  { id: 4, title: 'Quiz 2: อัลกอริทึม', course: 'CS3301', questions: 20, status: 'draft', date: '5 มิ.ย. 2567' },
];

const MOCK_COURSES = [
  { id: 1, code: 'ENG2101', name: 'คณิตศาสตร์วิศวกรรม I', students: 45, exams: 5, color: '#6366f1' },
  { id: 2, code: 'CS2203', name: 'โครงสร้างข้อมูล', students: 38, exams: 7, color: '#8b5cf6' },
  { id: 3, code: 'SCI1101', name: 'ฟิสิกส์ทั่วไป', students: 59, exams: 4, color: '#0ea5e9' },
  { id: 4, code: 'CS3301', name: 'อัลกอริทึมและความซับซ้อน', students: 30, exams: 8, color: '#10b981' },
];

// ─── Types ────────────────────────────────────────────────────────────────────
interface Stat { label: string; value: number; icon: React.ReactNode; color: string; bg: string; suffix?: string; }
interface Exam { id: number; title: string; course: string; questions: number; status: string; date: string; }
interface Course { id: number; code: string; name: string; students: number; exams: number; color: string; }

// ─── Animated counter ─────────────────────────────────────────────────────────
function useCounter(target: number, duration = 1200) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setCount(target); clearInterval(timer); }
      else setCount(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration]);
  return count;
}

// ─── Stat Card ────────────────────────────────────────────────────────────────
function StatCard({ label, value, icon, color, bg, suffix = '' }: Stat) {
  const count = useCounter(value);
  return (
    <div style={{
      background: '#fff',
      borderRadius: 20,
      padding: '24px 28px',
      display: 'flex',
      alignItems: 'center',
      gap: 20,
      boxShadow: '0 2px 16px rgba(0,0,0,0.06)',
      border: '1px solid #f1f5f9',
      transition: 'transform 0.2s, box-shadow 0.2s',
      cursor: 'default',
    }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-3px)';
        (e.currentTarget as HTMLDivElement).style.boxShadow = '0 8px 32px rgba(0,0,0,0.10)';
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)';
        (e.currentTarget as HTMLDivElement).style.boxShadow = '0 2px 16px rgba(0,0,0,0.06)';
      }}
    >
      <div style={{ width: 56, height: 56, borderRadius: 16, background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 13, color: '#94a3b8', fontWeight: 500, marginBottom: 4 }}>{label}</div>
        <div style={{ fontSize: 32, fontWeight: 800, color: '#1e293b', lineHeight: 1, letterSpacing: '-1px' }}>
          {count.toLocaleString()}<span style={{ fontSize: 16, fontWeight: 600, color }}>{suffix}</span>
        </div>
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
function DashboardContent() {
  const [activeNav, setActiveNav] = useState('dashboard');

  const stats: Stat[] = [
    { label: 'รายวิชาในระบบ', value: MOCK_STATS.totalCourses, icon: <BookOpen size={24} />, color: '#6366f1', bg: '#eef2ff' },
    { label: 'ชุดข้อสอบทั้งหมด', value: MOCK_STATS.totalExams, icon: <ClipboardList size={24} />, color: '#8b5cf6', bg: '#f5f3ff' },
    { label: 'จำนวนข้อสอบ (ข้อ)', value: MOCK_STATS.totalQuestions, icon: <FileText size={24} />, color: '#0ea5e9', bg: '#f0f9ff' },
    { label: 'นักศึกษาทั้งหมด', value: MOCK_STATS.activeStudents, icon: <Users size={24} />, color: '#10b981', bg: '#ecfdf5' },
  ];

  const navItems = [
    { key: 'dashboard', label: 'ภาพรวม', icon: <LayoutDashboard size={18} /> },
    { key: 'courses', label: 'รายวิชา', icon: <BookOpen size={18} /> },
    { key: 'exams', label: 'ข้อสอบ', icon: <ClipboardList size={18} /> },
    { key: 'questions', label: 'คลังข้อสอบ', icon: <FileText size={18} /> },
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Sarabun', sans-serif; background: #f8fafc; }
        .dashboard-root { display: flex; min-height: 100vh; font-family: 'Sarabun', sans-serif; }

        /* Sidebar */
        .sidebar {
          width: 240px; flex-shrink: 0;
          background: #fff;
          border-right: 1px solid #f1f5f9;
          display: flex; flex-direction: column;
          position: fixed; top: 0; left: 0; height: 100vh;
          z-index: 10;
        }
        .sidebar-logo {
          display: flex; align-items: center; gap: 12px;
          padding: 24px 20px 20px;
          border-bottom: 1px solid #f1f5f9;
        }
        .logo-icon {
          width: 40px; height: 40px; border-radius: 12px;
          background: linear-gradient(135deg, #4f46e5, #7c3aed);
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
        }
        .logo-text { font-size: 15px; font-weight: 700; color: #1e293b; line-height: 1.2; }
        .logo-sub { font-size: 11px; color: #94a3b8; font-weight: 400; }

        .nav { flex: 1; padding: 16px 12px; display: flex; flex-direction: column; gap: 2px; }
        .nav-item {
          display: flex; align-items: center; gap: 10px;
          padding: 10px 12px; border-radius: 10px;
          font-size: 14px; font-weight: 500; color: #64748b;
          cursor: pointer; transition: all 0.15s; border: none; background: none;
          font-family: 'Sarabun', sans-serif; width: 100%; text-align: left;
        }
        .nav-item:hover { background: #f8fafc; color: #1e293b; }
        .nav-item.active { background: #eef2ff; color: #4f46e5; font-weight: 600; }
        .nav-item.active svg { color: #4f46e5; }

        .sidebar-footer {
          padding: 16px 12px;
          border-top: 1px solid #f1f5f9;
        }
        .user-card {
          display: flex; align-items: center; gap: 10px;
          padding: 10px 12px; border-radius: 12px;
          background: #f8fafc; margin-bottom: 8px;
        }
        .avatar {
          width: 36px; height: 36px; border-radius: 10px;
          background: linear-gradient(135deg, #4f46e5, #7c3aed);
          display: flex; align-items: center; justify-content: center;
          color: #fff; font-weight: 700; font-size: 14px; flex-shrink: 0;
        }
        .user-name { font-size: 13px; font-weight: 600; color: #1e293b; }
        .user-role { font-size: 11px; color: #94a3b8; }
        .btn-logout {
          display: flex; align-items: center; gap: 8px;
          width: 100%; padding: 9px 12px; border-radius: 10px;
          background: none; border: none; cursor: pointer;
          font-family: 'Sarabun', sans-serif; font-size: 13px;
          color: #94a3b8; transition: all 0.15s; font-weight: 500;
        }
        .btn-logout:hover { background: #fef2f2; color: #ef4444; }

        /* Main */
        .main { margin-left: 240px; flex: 1; display: flex; flex-direction: column; min-height: 100vh; }

        /* Topbar */
        .topbar {
          height: 64px; background: #fff;
          border-bottom: 1px solid #f1f5f9;
          display: flex; align-items: center; justify-content: space-between;
          padding: 0 32px; position: sticky; top: 0; z-index: 5;
        }
        .topbar-title { font-size: 20px; font-weight: 700; color: #1e293b; }
        .topbar-sub { font-size: 13px; color: #94a3b8; margin-top: 2px; }
        .topbar-right { display: flex; align-items: center; gap: 12px; }
        .btn-notif {
          width: 40px; height: 40px; border-radius: 10px;
          background: #f8fafc; border: 1px solid #f1f5f9;
          display: flex; align-items: center; justify-content: center;
          cursor: pointer; color: #64748b; transition: all 0.15s; position: relative;
        }
        .btn-notif:hover { background: #eef2ff; color: #4f46e5; }
        .notif-dot {
          position: absolute; top: 8px; right: 8px;
          width: 7px; height: 7px; border-radius: 50%;
          background: #ef4444; border: 2px solid #fff;
        }
        .btn-new-exam {
          display: flex; align-items: center; gap: 8px;
          padding: 9px 18px; border-radius: 10px;
          background: linear-gradient(135deg, #4f46e5, #7c3aed);
          color: #fff; border: none; cursor: pointer;
          font-family: 'Sarabun', sans-serif; font-size: 14px; font-weight: 600;
          box-shadow: 0 4px 14px rgba(99,102,241,0.3); transition: all 0.2s;
        }
        .btn-new-exam:hover { opacity: 0.9; box-shadow: 0 6px 20px rgba(99,102,241,0.4); }

        /* Content */
        .content { padding: 32px; flex: 1; }

        /* Stats grid */
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 20px;
          margin-bottom: 32px;
        }

        /* Section */
        .section-title {
          font-size: 16px; font-weight: 700; color: #1e293b;
          margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;
        }
        .see-all { font-size: 13px; font-weight: 500; color: #6366f1; cursor: pointer; display: flex; align-items: center; gap: 4px; }
        .see-all:hover { text-decoration: underline; }

        /* Two col layout */
        .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }

        /* Exam list */
        .card-box {
          background: #fff; border-radius: 20px;
          border: 1px solid #f1f5f9;
          box-shadow: 0 2px 16px rgba(0,0,0,0.04);
          overflow: hidden;
        }
        .card-box-header { padding: 20px 24px 16px; border-bottom: 1px solid #f8fafc; }
        .exam-item {
          display: flex; align-items: center; gap: 14px;
          padding: 14px 24px;
          border-bottom: 1px solid #f8fafc;
          transition: background 0.15s; cursor: pointer;
        }
        .exam-item:last-child { border-bottom: none; }
        .exam-item:hover { background: #f8fafc; }
        .exam-icon {
          width: 40px; height: 40px; border-radius: 12px;
          background: #eef2ff; display: flex; align-items: center;
          justify-content: center; flex-shrink: 0; color: #6366f1;
        }
        .exam-title { font-size: 14px; font-weight: 600; color: #1e293b; }
        .exam-meta { font-size: 12px; color: #94a3b8; margin-top: 2px; }
        .exam-right { margin-left: auto; display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
        .badge-status {
          display: inline-flex; align-items: center; gap: 4px;
          padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600;
        }
        .badge-published { background: #ecfdf5; color: #065f46; }
        .badge-draft { background: #f8fafc; color: #94a3b8; border: 1px solid #e2e8f0; }
        .exam-date { font-size: 11px; color: #cbd5e1; }

        /* Course cards */
        .course-item {
          display: flex; align-items: center; gap: 14px;
          padding: 14px 24px;
          border-bottom: 1px solid #f8fafc;
          transition: background 0.15s; cursor: pointer;
        }
        .course-item:last-child { border-bottom: none; }
        .course-item:hover { background: #f8fafc; }
        .course-dot { width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; color: #fff; flex-shrink: 0; }
        .course-name { font-size: 14px; font-weight: 600; color: #1e293b; }
        .course-meta { font-size: 12px; color: #94a3b8; margin-top: 2px; }
        .course-right { margin-left: auto; text-align: right; }
        .course-exam-count { font-size: 20px; font-weight: 800; color: #1e293b; line-height: 1; }
        .course-exam-label { font-size: 11px; color: #94a3b8; }

        /* Progress bar */
        .progress-wrap { margin-top: 24px; }
        .progress-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
        .progress-label { font-size: 13px; color: #64748b; font-weight: 500; }
        .progress-val { font-size: 13px; font-weight: 700; color: #1e293b; }
        .progress-bar { height: 8px; background: #f1f5f9; border-radius: 99px; overflow: hidden; margin-bottom: 16px; }
        .progress-fill { height: 100%; border-radius: 99px; }

        @media (max-width: 1100px) {
          .stats-grid { grid-template-columns: repeat(2, 1fr); }
          .two-col { grid-template-columns: 1fr; }
        }
        @media (max-width: 768px) {
          .sidebar { display: none; }
          .main { margin-left: 0; }
          .stats-grid { grid-template-columns: 1fr 1fr; }
          .content { padding: 20px; }
        }
      `}</style>

      <div className="dashboard-root">
        {/* ── Sidebar ── */}
        <aside className="sidebar">
          <div className="sidebar-logo">
            <div className="logo-icon">
              <BookOpen size={20} color="#fff" />
            </div>
            <div>
              <div className="logo-text">Teacher Portal</div>
              <div className="logo-sub">ระบบจัดการข้อสอบ</div>
            </div>
          </div>

          <nav className="nav">
            {navItems.map(item => (
              <button key={item.key} className={`nav-item ${activeNav === item.key ? 'active' : ''}`} onClick={() => setActiveNav(item.key)}>
                {item.icon}
                {item.label}
              </button>
            ))}
          </nav>

          <div className="sidebar-footer">
            <div className="user-card">
              <div className="avatar">อ</div>
              <div>
                <div className="user-name">อ.สมชาย ใจดี</div>
                <div className="user-role">อาจารย์ผู้สอน</div>
              </div>
            </div>
            <button className="btn-logout" onClick={() => {
              localStorage.removeItem('authToken');
              localStorage.removeItem('refreshToken');
              localStorage.removeItem('user');
              window.location.href = '/';
            }}>
              <LogOut size={15} /> ออกจากระบบ
            </button>
          </div>
        </aside>

        {/* ── Main ── */}
        <div className="main">
          {/* Topbar */}
          <header className="topbar">
            <div>
              <div className="topbar-title">ภาพรวมระบบ</div>
              <div className="topbar-sub">ภาคเรียนที่ 1 ปีการศึกษา 2567</div>
            </div>
            <div className="topbar-right">
              <button className="btn-notif">
                <Bell size={18} />
                <span className="notif-dot" />
              </button>
              <button className="btn-new-exam">
                + สร้างข้อสอบ
              </button>
            </div>
          </header>

          {/* Content */}
          <div className="content">

            {/* Stats */}
            <div className="stats-grid">
              {stats.map((s, i) => <StatCard key={i} {...s} />)}
            </div>

            {/* Two col */}
            <div className="two-col">
              {/* Recent exams */}
              <div>
                <div className="section-title">
                  ข้อสอบล่าสุด
                  <span className="see-all">ดูทั้งหมด <ChevronRight size={14} /></span>
                </div>
                <div className="card-box">
                  {(MOCK_RECENT_EXAMS as Exam[]).map(exam => (
                    <div key={exam.id} className="exam-item">
                      <div className="exam-icon">
                        <ClipboardList size={18} />
                      </div>
                      <div>
                        <div className="exam-title">{exam.title}</div>
                        <div className="exam-meta">{exam.course} · {exam.questions} ข้อ</div>
                      </div>
                      <div className="exam-right">
                        <span className={`badge-status ${exam.status === 'published' ? 'badge-published' : 'badge-draft'}`}>
                          {exam.status === 'published'
                            ? <><CheckCircle size={10} /> เผยแพร่แล้ว</>
                            : <><Clock size={10} /> ฉบับร่าง</>
                          }
                        </span>
                        <span className="exam-date">{exam.date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Courses */}
              <div>
                <div className="section-title">
                  รายวิชาของฉัน
                  <span className="see-all">จัดการ <ChevronRight size={14} /></span>
                </div>
                <div className="card-box">
                  {(MOCK_COURSES as Course[]).map(c => (
                    <div key={c.id} className="course-item">
                      <div className="course-dot" style={{ background: c.color }}>
                        {c.code.slice(0, 3)}
                      </div>
                      <div>
                        <div className="course-name">{c.name}</div>
                        <div className="course-meta">{c.code} · {c.students} คน</div>
                      </div>
                      <div className="course-right">
                        <div className="course-exam-count">{c.exams}</div>
                        <div className="course-exam-label">ข้อสอบ</div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Progress section */}
                <div className="card-box" style={{ marginTop: 24, padding: '20px 24px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <TrendingUp size={16} color="#6366f1" />
                    <span style={{ fontSize: 14, fontWeight: 700, color: '#1e293b' }}>สัดส่วนข้อสอบต่อวิชา</span>
                  </div>
                  {(MOCK_COURSES as Course[]).map(c => (
                    <div key={c.id}>
                      <div className="progress-row">
                        <span className="progress-label">{c.code}</span>
                        <span className="progress-val">{c.exams} ชุด</span>
                      </div>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${(c.exams / MOCK_STATS.totalExams) * 100}%`, background: c.color }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Export with protection ────────────────────────────────────────────────────
export default function Dashboard() {
  return (
    <ProtectedRoute requiredRole="teacher">
      <DashboardContent />
    </ProtectedRoute>
  );
}
