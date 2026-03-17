"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  BookOpen, 
  FileText, 
  ClipboardList, 
  LogOut, 
  Bell, 
  Plus, 
  Eye, 
  Edit, 
  Trash2,
  CheckCircle,
  Clock
} from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { examApi } from '@/lib/api';
import { ExamResponse } from '@/types/exam';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

// ─── Mock Data (fallback) ─────────────────────────────────────────────────────
const MOCK_EXAMS: ExamResponse[] = [
  {
    id: '1',
    title: 'Midterm: คณิตศาสตร์วิศวกรรม I',
    subject: 'ENG2101',
    description: 'บทที่ 1-5',
    created_by: 'user-1',
    total_questions: 40,
    created_at: '2026-03-10T10:00:00Z',
    updated_at: '2026-03-10T10:00:00Z',
  },
  {
    id: '2',
    title: 'Quiz 3: โครงสร้างข้อมูล',
    subject: 'CS2203',
    description: 'Tree and Graph algorithms',
    created_by: 'user-1',
    total_questions: 15,
    created_at: '2026-03-08T14:30:00Z',
    updated_at: '2026-03-08T14:30:00Z',
  },
  {
    id: '3',
    title: 'Final: ฟิสิกส์ทั่วไป',
    subject: 'SCI1101',
    description: 'บทที่ 1-8',
    created_by: 'user-1',
    total_questions: 60,
    created_at: '2026-03-05T09:15:00Z',
    updated_at: '2026-03-05T09:15:00Z',
  },
];

// ─── Types ────────────────────────────────────────────────────────────────────
interface ExamWithStatus extends ExamResponse {
  status: 'draft' | 'published' | 'graded';
}

interface Stat {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  bg: string;
  suffix?: string;
}

// ─── Stat Card Component ──────────────────────────────────────────────────────
function StatCard({ label, value, icon, color, bg, suffix = '' }: Stat) {
  return (
    <div className="bg-white rounded-2xl p-6 flex items-center gap-5 shadow-sm border border-slate-100 transition-all duration-200 hover:-translate-y-1 hover:shadow-md cursor-default">
      <div 
        className="w-14 h-14 rounded-xl flex items-center justify-center shrink-0"
        style={{ backgroundColor: bg, color: color }}
      >
        {icon}
      </div>
      <div>
        <div className="text-sm text-slate-500 font-medium mb-1">{label}</div>
        <div className="text-3xl font-extrabold text-slate-800 tracking-tight flex items-baseline gap-1">
          {value.toLocaleString()}
          <span className="text-base font-semibold" style={{ color }}>{suffix}</span>
        </div>
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
function DashboardContent() {
  const router = useRouter();
  const [exams, setExams] = useState<ExamWithStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch exams on mount
  useEffect(() => {
    const fetchExams = async () => {
      try {
        setLoading(true);
        const response = await examApi.getExams();
        // Add mock status for now
        const examsWithStatus: ExamWithStatus[] = response.exams.map((exam) => ({
          ...exam,
          status: (Math.random() > 0.5 ? 'published' : 'draft') as 'draft' | 'published',
        }));
        setExams(examsWithStatus);
      } catch (err) {
        console.warn('API not ready, using mock data:', err);

        // Fallback to mock data stored in localStorage (for offline/mock UI flows)
        const storedExams = typeof window !== 'undefined' ? localStorage.getItem('mockExams') : null;
        const parsedExams = storedExams ? JSON.parse(storedExams) : null;
        const sourceExams: ExamResponse[] = Array.isArray(parsedExams) ? parsedExams : MOCK_EXAMS;

        setExams(sourceExams.map((exam) => ({
          ...exam,
          status: (Math.random() > 0.5 ? 'published' : 'draft') as 'draft' | 'published',
        })));
      } finally {
        setLoading(false);
      }
    };

    fetchExams();
  }, []);

  const handleViewExam = (examId: string) => router.push(`/exams/${examId}`);
  const handleEditExam = (examId: string) => router.push(`/exams/${examId}/edit`);

  const handleDeleteExam = async (examId: string) => {
    if (!confirm('คุณแน่ใจหรือไม่ว่าต้องการลบข้อสอบชุดนี้?')) return;

    try {
      await examApi.deleteExam(examId);
      setExams(exams.filter((exam) => exam.id !== examId));
    } catch (err) {
      console.error('Failed to delete exam:', err);
      alert('เกิดข้อผิดพลาดในการลบข้อสอบ');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('th-TH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    window.location.href = '/';
  };

  // Calculate stats from exams array
  const totalExams = exams.length;
  const publishedExams = exams.filter(e => e.status === 'published').length;
  const draftExams = exams.filter(e => e.status === 'draft').length;

  return (
    <div className="flex min-h-screen bg-slate-50 font-sans">
      
      {/* ── Sidebar ── */}
      <aside className="w-64 shrink-0 bg-white border-r border-slate-100 flex flex-col fixed inset-y-0 left-0 z-10">
        <div className="flex items-center gap-3 px-6 py-6 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shrink-0 shadow-sm">
            <BookOpen size={20} className="text-white" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-800 leading-tight">Teacher Portal</div>
            <div className="text-xs text-slate-400 font-medium">ระบบจัดการข้อสอบ</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
          <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold bg-indigo-50 text-indigo-600 w-full text-left transition-colors">
            <ClipboardList size={18} />
            ข้อสอบทั้งหมด
          </button>
          <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-500 hover:bg-slate-50 hover:text-slate-800 w-full text-left transition-colors">
            <BookOpen size={18} />
            รายวิชา
          </button>
          <button className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-500 hover:bg-slate-50 hover:text-slate-800 w-full text-left transition-colors">
            <FileText size={18} />
            คลังข้อสอบ
          </button>
        </nav>

        <div className="p-4 border-t border-slate-100 flex flex-col gap-3">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 text-white font-semibold flex items-center justify-center text-sm">
              อ
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-800">อ.สมชาย ใจดี</div>
              <div className="text-xs text-slate-500">อาจารย์ผู้สอน</div>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-slate-500 hover:bg-red-50 hover:text-red-600 transition-colors w-full"
          >
            <LogOut size={16} /> ออกจากระบบ
          </button>
        </div>
      </aside>

      {/* ── Main Area ── */}
      <div className="flex-1 ml-64 flex flex-col">
        {/* Topbar */}
        <header className="flex items-center justify-between px-8 py-6 bg-white border-b border-slate-100 sticky top-0 z-10">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-800">ภาพรวมการจัดการข้อสอบ</h1>
            <p className="text-sm text-slate-500 mt-1">จัดการและตรวจสอบข้อสอบของคุณในที่เดียว</p>
          </div>
          <div className="flex items-center gap-4">
            <button className="w-10 h-10 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-100 flex items-center justify-center relative transition-colors">
              <Bell size={18} className="text-slate-600" />
              <span className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-red-500 border-2 border-white" />
            </button>
            <Button 
              className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-md shadow-indigo-200 border-0 rounded-xl px-5 gap-2"
              onClick={() => router.push('/exams/create')}
            >
              <Plus size={18} />
              สร้างข้อสอบใหม่
            </Button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-8">
          
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <StatCard 
              label="ข้อสอบทั้งหมด" 
              value={totalExams} 
              icon={<ClipboardList size={24} />} 
              color="#4f46e5" 
              bg="#e0e7ff" 
              suffix=" ชุด" 
            />
            <StatCard 
              label="เผยแพร่แล้ว" 
              value={publishedExams} 
              icon={<CheckCircle size={24} />} 
              color="#16a34a" 
              bg="#dcfce7" 
              suffix=" ชุด" 
            />
            <StatCard 
              label="ฉบับร่าง" 
              value={draftExams} 
              icon={<Clock size={24} />} 
              color="#ea580c" 
              bg="#ffedd5" 
              suffix=" ชุด" 
            />
          </div>

          {/* Table Section */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
              <h2 className="text-lg font-bold text-slate-800">รายการข้อสอบล่าสุด</h2>
            </div>
            
            <div className="p-2">
              {loading ? (
                <div className="text-center py-16 text-slate-500">กำลังโหลดข้อมูล...</div>
              ) : error ? (
                <div className="text-center py-16 text-red-500">{error}</div>
              ) : exams.length === 0 ? (
                <div className="text-center py-16 text-slate-500">ยังไม่มีข้อมูลข้อสอบ</div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead className="font-semibold text-slate-600">ชื่อข้อสอบ</TableHead>
                      <TableHead className="font-semibold text-slate-600">วิชา</TableHead>
                      <TableHead className="font-semibold text-slate-600">จำนวนข้อ</TableHead>
                      <TableHead className="font-semibold text-slate-600">สถานะ</TableHead>
                      <TableHead className="font-semibold text-slate-600">สร้างเมื่อ</TableHead>
                      <TableHead className="font-semibold text-slate-600 text-right pr-6">การจัดการ</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {exams.map((exam) => (
                      <TableRow key={exam.id} className="group">
                        <TableCell className="font-medium text-slate-800">{exam.title}</TableCell>
                        <TableCell className="text-slate-600">
                          <span className="bg-slate-100 px-2.5 py-1 rounded-md text-xs font-semibold">{exam.subject}</span>
                        </TableCell>
                        <TableCell className="text-slate-600">{exam.total_questions} ข้อ</TableCell>
                        <TableCell>
                          <Badge 
                            variant={exam.status === 'published' ? 'default' : 'secondary'}
                            className={exam.status === 'published' 
                              ? 'bg-green-100 text-green-700 hover:bg-green-200 border-0' 
                              : 'bg-orange-100 text-orange-700 hover:bg-orange-200 border-0'}
                          >
                            {exam.status === 'published' ? 'เผยแพร่แล้ว' : 'ฉบับร่าง'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate-500 text-sm">{formatDate(exam.created_at)}</TableCell>
                        <TableCell className="text-right pr-4">
                          <div className="flex items-center justify-end gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 hover:text-indigo-600" onClick={() => handleViewExam(exam.id)}>
                              <Eye size={16} />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 hover:text-amber-600" onClick={() => handleEditExam(exam.id)}>
                              <Edit size={16} />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 hover:text-red-600 hover:bg-red-50" onClick={() => handleDeleteExam(exam.id)}>
                              <Trash2 size={16} />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          </div>
          
        </main>
      </div>
    </div>
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