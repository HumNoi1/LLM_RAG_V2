"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Trash2, ArrowLeft } from "lucide-react";
import { examApi } from "@/lib/api";
import api from "@/lib/api";

interface QuestionFormItem {
  id: string;
  question_text: string;
  max_score: number;
}

export default function CreateExamPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [questions, setQuestions] = useState<QuestionFormItem[]>([
    { id: crypto.randomUUID(), question_text: "", max_score: 1 },
  ]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const updateQuestion = (id: string, field: keyof QuestionFormItem, value: string | number) => {
    setQuestions((prev) =>
      prev.map((q) => (q.id === id ? { ...q, [field]: value } : q))
    );
  };

  const addQuestion = () => {
    setQuestions((prev) => [
      ...prev,
      { id: crypto.randomUUID(), question_text: "", max_score: 1 },
    ]);
  };

  const removeQuestion = (id: string) => {
    setQuestions((prev) => prev.filter((q) => q.id !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!title.trim() || !subject.trim()) {
      setError("กรุณากรอกชื่อข้อสอบและวิชา");
      return;
    }

    if (questions.length === 0) {
      setError("กรุณาเพิ่มคำถามอย่างน้อย 1 ข้อ");
      return;
    }

    if (questions.some((q) => !q.question_text.trim())) {
      setError("กรุณากรอกคำถามทุกข้อ");
      return;
    }

    setSaving(true);

    try {
      // 1. Create the exam
      const exam = await examApi.createExam({
        title: title.trim(),
        subject: subject.trim(),
        description: description.trim() || undefined,
        total_questions: questions.length,
      });

      // 2. Add each question
      await Promise.all(
        questions.map((q, idx) =>
          api.post(`/exams/${exam.id}/questions`, {
            question_number: idx + 1,
            question_text: q.question_text.trim(),
            max_score: q.max_score,
          })
        )
      );

      router.push("/dashboard");
    } catch (err) {
      setError("เกิดข้อผิดพลาดในการสร้างข้อสอบ กรุณาลองใหม่อีกครั้ง");
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto w-full max-w-4xl">
        <div className="flex items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">
              สร้างข้อสอบใหม่
            </h1>
            <p className="text-sm text-slate-600">
              กรอกข้อมูลข้อสอบ และเพิ่มคำถามในรูปแบบ dynamic
            </p>
          </div>
          <Button variant="secondary" onClick={() => router.push("/dashboard")}> 
            <ArrowLeft size={16} />
            กลับไปยังหน้าหลัก
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 rounded-xl bg-white p-6 shadow-sm">
          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                ชื่อข้อสอบ
              </label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="เช่น Midterm Exam"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                วิชา
              </label>
              <Input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="เช่น CS2203"
              />
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">
              คำอธิบาย (ไม่บังคับ)
            </label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="อธิบายเนื้อหาหรือคำแนะนำสำหรับข้อสอบ"
              className="min-h-[120px]"
            />
          </div>

          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">คำถาม</h2>
            <Button type="button" variant="outline" size="sm" onClick={addQuestion}>
              <Plus size={14} /> เพิ่มคำถาม
            </Button>
          </div>

          <div className="space-y-4">
            {questions.map((question, idx) => (
              <div key={question.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-sm font-medium text-slate-700">
                      ข้อที่ {idx + 1}
                    </div>
                    <div className="mt-2">
                      <Input
                        value={question.question_text}
                        onChange={(e) => updateQuestion(question.id, "question_text", e.target.value)}
                        placeholder="พิมพ์คำถามที่นี่"
                      />
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-2">
                    <div className="flex items-center gap-2">
                      <label className="text-sm font-medium text-slate-600">
                        คะแนนสูงสุด
                      </label>
                      <Input
                        type="number"
                        min={1}
                        value={question.max_score}
                        onChange={(e) =>
                          updateQuestion(question.id, "max_score", Number(e.target.value))
                        }
                        className="w-20"
                      />
                    </div>
                    {questions.length > 1 ? (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => removeQuestion(question.id)}
                      >
                        <Trash2 size={14} />
                        ลบ
                      </Button>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => router.push("/dashboard")} type="button">
              ยกเลิก
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "กำลังบันทึก..." : "สร้างข้อสอบ"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
