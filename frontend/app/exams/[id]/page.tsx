"use client";

import React, { useEffect, useMemo, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileText, FolderOpen, ListChecks, ClipboardList, Upload, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PdfPreview } from "@/components/PdfPreview";
import api from "@/lib/api";
import type { SubmissionSummary } from "@/types/document";

type TabKey = "info" | "documents" | "answers" | "grading";

interface StoredExam {
  id: string;
  title: string;
  subject: string;
  description: string | null;
  created_by: string;
  total_questions: number;
  created_at: string;
  updated_at: string;
}

interface StoredQuestion {
  question_number: number;
  question_text: string;
  max_score: number;
}

interface StoredDocument {
  id: string;
  type: "answer_key" | "rubric" | "course_material";
  name: string;
  status: "uploaded" | "pending";
  uploaded_at: string;
  dataUrl?: string; // used for preview
}

export default function ExamDetailPage() {
  const { id } = useParams() as { id?: string };
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabKey>("info");
  const [exam, setExam] = useState<StoredExam | null>(null);
  const [questions, setQuestions] = useState<StoredQuestion[]>([]);
  const [documents, setDocuments] = useState<StoredDocument[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Student submissions state
  const [submissions, setSubmissions] = useState<SubmissionSummary[]>([]);
  const [submissionsLoading, setSubmissionsLoading] = useState(false);
  const [submissionsError, setSubmissionsError] = useState<string | null>(null);
  const [uploadStudentId, setUploadStudentId] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError("ไม่พบรหัสข้อสอบ");
      return;
    }

    const storedExams = typeof window !== "undefined" ? localStorage.getItem("mockExams") : null;
    const parsedExams = storedExams ? JSON.parse(storedExams) : null;

    if (!Array.isArray(parsedExams)) {
      setError("ไม่พบข้อมูลข้อสอบ");
      return;
    }

    const found = parsedExams.find((e: StoredExam) => e.id === id);
    if (!found) {
      setError("ไม่พบข้อมูลข้อสอบ");
      return;
    }

    setExam(found);

    const storedQuestions = typeof window !== "undefined" ? localStorage.getItem(`mockExamQuestions_${id}`) : null;
    const parsedQuestions = storedQuestions ? JSON.parse(storedQuestions) : null;
    setQuestions(Array.isArray(parsedQuestions) ? parsedQuestions : []);

    const storedDocs = typeof window !== "undefined" ? localStorage.getItem(`mockExamDocuments_${id}`) : null;
    const parsedDocs = storedDocs ? JSON.parse(storedDocs) : null;
    setDocuments(Array.isArray(parsedDocs) ? parsedDocs : []);
  }, [id]);

  const fetchSubmissions = useCallback(async () => {
    if (!id) return;
    setSubmissionsLoading(true);
    setSubmissionsError(null);
    try {
      const resp = await api.get(`/documents/submissions?exam_id=${id}`);
      setSubmissions(resp.data.submissions ?? []);
    } catch {
      setSubmissionsError("ไม่สามารถโหลดรายการคำตอบได้");
    } finally {
      setSubmissionsLoading(false);
    }
  }, [id]);

  // Auto-load submissions when navigating to the answers tab
  useEffect(() => {
    if (activeTab === "answers") {
      fetchSubmissions();
    }
  }, [activeTab, fetchSubmissions]);

  const handleSubmissionUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadStudentId.trim() || !id) return;
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    try {
      const formData = new FormData();
      formData.append("exam_id", id);
      formData.append("student_id", uploadStudentId.trim());
      formData.append("file", uploadFile);
      await api.post("/documents/submissions/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadSuccess("อัปโหลดสำเร็จ กำลังประมวลผล...");
      setUploadFile(null);
      setUploadStudentId("");
      fetchSubmissions();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "เกิดข้อผิดพลาดในการอัปโหลด";
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  const tabs = useMemo(
    () => [
      { key: "info" as TabKey, label: "ข้อมูลข้อสอบ", icon: <FileText size={16} /> },
      { key: "documents" as TabKey, label: "เอกสาร", icon: <FolderOpen size={16} /> },
      { key: "answers" as TabKey, label: "คำตอบนักศึกษา", icon: <ListChecks size={16} /> },
      { key: "grading" as TabKey, label: "การให้คะแนน", icon: <ClipboardList size={16} /> },
    ],
    []
  );

  const saveDocuments = (docs: StoredDocument[]) => {
    setDocuments(docs);
    if (typeof window !== "undefined" && id) {
      localStorage.setItem(`mockExamDocuments_${id}`, JSON.stringify(docs));
    }
  };

  const addDocument = async (type: StoredDocument["type"], file: File) => {
    const doc: StoredDocument = {
      id: crypto.randomUUID(),
      type,
      name: file.name,
      status: "uploaded",
      uploaded_at: new Date().toISOString(),
    };

    // If it's a PDF, create a data URL for preview (mock only)
    if (file.type === "application/pdf") {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === "string") {
          saveDocuments([{ ...doc, dataUrl: reader.result }, ...documents]);
        } else {
          saveDocuments([doc, ...documents]);
        }
      };
      reader.readAsDataURL(file);
    } else {
      saveDocuments([doc, ...documents]);
    }
  };

  const [selectedPreviewDocId, setSelectedPreviewDocId] = useState<string | null>(null);

  const onDropFiles = (type: StoredDocument["type"], files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach((file) => addDocument(type, file));
  };


  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 p-6">
        <div className="mx-auto max-w-4xl rounded-xl border border-red-200 bg-white p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-semibold text-red-700">เกิดข้อผิดพลาด</h1>
              <p className="mt-2 text-sm text-red-600">{error}</p>
            </div>
            <Button variant="secondary" onClick={() => router.push("/dashboard")}>กลับไปหน้าหลัก</Button>
          </div>
        </div>
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="min-h-screen bg-slate-50 p-6">
        <div className="mx-auto max-w-4xl rounded-xl border border-slate-200 bg-white p-6">
          <div className="text-center text-slate-600">กำลังโหลดข้อมูลข้อสอบ...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 flex flex-col gap-4 rounded-xl bg-white p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="sm" onClick={() => router.push("/dashboard")}
                className="!px-2">
                <ArrowLeft size={16} />
              </Button>
              <div>
                <h1 className="text-2xl font-semibold text-slate-900">{exam.title}</h1>
                <p className="text-sm text-slate-600">{exam.subject}</p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${
                  activeTab === tab.key
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                <span className="flex-shrink-0">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm">
          {activeTab === "info" && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-slate-900">ข้อมูลข้อสอบ</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <div className="text-sm font-medium text-slate-600">ชื่อข้อสอบ</div>
                  <div className="mt-1 text-base text-slate-900">{exam.title}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-slate-600">วิชา</div>
                  <div className="mt-1 text-base text-slate-900">{exam.subject}</div>
                </div>
                <div className="md:col-span-2">
                  <div className="text-sm font-medium text-slate-600">คำอธิบาย</div>
                  <div className="mt-1 text-base text-slate-900">{exam.description ?? "ไม่มีคำอธิบาย"}</div>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-lg border border-slate-200 p-4">
                  <div className="text-xs font-medium text-slate-500">จำนวนคำถาม</div>
                  <div className="mt-2 text-2xl font-semibold text-slate-900">{exam.total_questions}</div>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                  <div className="text-xs font-medium text-slate-500">สร้างเมื่อ</div>
                  <div className="mt-2 text-base text-slate-900">
                    {new Date(exam.created_at).toLocaleString("th-TH", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                  <div className="text-xs font-medium text-slate-500">อัปเดตล่าสุด</div>
                  <div className="mt-2 text-base text-slate-900">
                    {new Date(exam.updated_at).toLocaleString("th-TH", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "documents" && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-slate-900">เอกสาร</h2>
              <p className="text-sm text-slate-600">
                อัปโหลดไฟล์สำหรับ key, rubric หรือเอกสารประกอบอื่น ๆ (เก็บแบบ mock ใน localStorage)
              </p>

              <div className="grid gap-6 md:grid-cols-3">
                {(
                  [
                    { key: "answer_key", label: "Answer Key" },
                    { key: "rubric", label: "Rubric" },
                    { key: "course_material", label: "Course Material" },
                  ] as const
                ).map((docType) => {
                  const existing = documents.find((d) => d.type === docType.key);
                  return (
                    <label
                      key={docType.key}
                      className="group flex flex-col rounded-xl border border-slate-200 bg-slate-50 p-4 text-left transition hover:border-indigo-400"
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        onDropFiles(docType.key, e.dataTransfer.files);
                      }}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-slate-900">{docType.label}</div>
                          <div className="text-xs text-slate-500">ลากวางไฟล์ หรือคลิกเพื่อเลือก</div>
                        </div>
                        <div
                          className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${
                            existing ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {existing ? "Uploaded" : "Pending"}
                        </div>
                      </div>

                      <input
                        type="file"
                        accept=".pdf,.doc,.docx"
                        className="sr-only"
                        onChange={(e) => onDropFiles(docType.key, e.target.files)}
                      />

                      <div className="mt-4 flex flex-col gap-3">
                        {existing ? (
                          <div className="rounded-lg border border-slate-200 bg-white p-3">
                            <div className="flex items-center justify-between gap-3">
                              <div>
                                <div className="text-sm font-medium text-slate-700">{existing.name}</div>
                                <div className="text-xs text-slate-500">
                                  อัปโหลดเมื่อ {new Date(existing.uploaded_at).toLocaleString("th-TH")}
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  saveDocuments(documents.filter((d) => d.id !== existing.id));
                                }}
                              >
                                ลบ
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="rounded-lg border border-dashed border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
                            ไม่มีไฟล์
                          </div>
                        )}
                      </div>
                    </label>
                  );
                })}
              </div>

              {documents.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-semibold text-slate-800">ไฟล์ที่อัปโหลด</div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        saveDocuments([]);
                        setSelectedPreviewDocId(null);
                      }}
                    >
                      ล้างทั้งหมด
                    </Button>
                  </div>
                  <div className="mt-3 space-y-2">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className={`flex cursor-pointer flex-col gap-1 rounded-lg border border-slate-200 bg-white p-3 transition hover:border-indigo-300 ${
                          selectedPreviewDocId === doc.id ? "ring-2 ring-indigo-200" : ""
                        }`}
                        onClick={() => setSelectedPreviewDocId(doc.id)}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <div className="text-sm font-medium text-slate-700">{doc.name}</div>
                            <div className="text-xs text-slate-500">{doc.type.replace("_", " ")}</div>
                          </div>
                          <div className="text-xs font-semibold text-emerald-700">{doc.status}</div>
                        </div>
                        <div className="flex items-center justify-between text-xs text-slate-500">
                          <span>อัปโหลด: {new Date(doc.uploaded_at).toLocaleString("th-TH")}</span>
                          <button
                            type="button"
                            className="text-indigo-600 hover:text-indigo-800"
                            onClick={(e) => {
                              e.stopPropagation();
                              saveDocuments(documents.filter((d) => d.id !== doc.id));
                              if (selectedPreviewDocId === doc.id) setSelectedPreviewDocId(null);
                            }}
                          >
                            ลบ
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedPreviewDocId && (
                <div className="mt-4">
                  {(() => {
                    const selected = documents.find((d) => d.id === selectedPreviewDocId);
                    if (!selected) return null;
                    if (selected.dataUrl) {
                      return <PdfPreview fileUrl={selected.dataUrl} />;
                    }
                    return (
                      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600">
                        ไม่มีตัวอย่างสำหรับไฟล์นี้
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          )}
          {activeTab === "answers" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">คำตอบนักศึกษา</h2>
                  <p className="text-sm text-slate-500">อัปโหลด PDF คำตอบของนักศึกษา (ต้องระบุ Student UUID)</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchSubmissions}
                  disabled={submissionsLoading}
                >
                  <RefreshCw size={14} className={submissionsLoading ? "animate-spin" : ""} />
                  รีเฟรช
                </Button>
              </div>

              {/* Upload form */}
              <form
                onSubmit={handleSubmissionUpload}
                className="rounded-xl border border-slate-200 bg-slate-50 p-5 space-y-4"
              >
                <h3 className="text-sm font-semibold text-slate-800">อัปโหลดคำตอบใหม่</h3>

                {uploadError ? (
                  <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {uploadError}
                  </div>
                ) : null}
                {uploadSuccess ? (
                  <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
                    {uploadSuccess}
                  </div>
                ) : null}

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">
                      Student UUID
                    </label>
                    <input
                      type="text"
                      value={uploadStudentId}
                      onChange={(e) => setUploadStudentId(e.target.value)}
                      placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                      required
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">
                      ไฟล์ PDF คำตอบ
                    </label>
                    <label
                      className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-slate-300 bg-white px-3 py-2 text-sm text-slate-600 hover:border-indigo-400 transition"
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        const f = e.dataTransfer.files[0];
                        if (f) setUploadFile(f);
                      }}
                    >
                      <Upload size={14} />
                      {uploadFile ? uploadFile.name : "ลากวางหรือคลิกเพื่อเลือกไฟล์"}
                      <input
                        type="file"
                        accept=".pdf"
                        className="sr-only"
                        onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
                        required
                      />
                    </label>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button
                    type="submit"
                    disabled={uploading || !uploadFile || !uploadStudentId.trim()}
                  >
                    {uploading ? "กำลังอัปโหลด..." : "อัปโหลด"}
                  </Button>
                </div>
              </form>

              {/* Submission list */}
              <div>
                <h3 className="mb-3 text-sm font-semibold text-slate-800">
                  รายการที่ส่งแล้ว ({submissions.length})
                </h3>

                {submissionsError ? (
                  <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {submissionsError}
                  </div>
                ) : submissions.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-500">
                    {submissionsLoading ? "กำลังโหลด..." : "ยังไม่มีคำตอบที่ส่ง"}
                  </div>
                ) : (
                  <div className="overflow-x-auto rounded-xl border border-slate-200">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 text-xs font-semibold text-slate-600">
                        <tr>
                          <th className="px-4 py-3 text-left">ชื่อนักศึกษา</th>
                          <th className="px-4 py-3 text-left">รหัสนักศึกษา</th>
                          <th className="px-4 py-3 text-left">สถานะ</th>
                          <th className="px-4 py-3 text-right">คะแนน</th>
                          <th className="px-4 py-3 text-right">ตรวจแล้ว</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {submissions.map((sub) => (
                          <tr key={sub.id} className="hover:bg-slate-50">
                            <td className="px-4 py-3 font-medium text-slate-800">
                              {sub.student_name || "—"}
                            </td>
                            <td className="px-4 py-3 text-slate-600">
                              {sub.student_code || "—"}
                            </td>
                            <td className="px-4 py-3">
                              <span
                                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                                  sub.status === "graded"
                                    ? "bg-emerald-100 text-emerald-700"
                                    : sub.status === "parsed"
                                    ? "bg-blue-100 text-blue-700"
                                    : "bg-slate-100 text-slate-600"
                                }`}
                              >
                                {sub.status}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right text-slate-800">
                              {sub.total_score != null
                                ? `${sub.total_score} / ${sub.max_total_score}`
                                : "—"}
                            </td>
                            <td className="px-4 py-3 text-right text-slate-600">
                              {sub.graded_questions} / {sub.total_questions}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === "grading" && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-slate-900">การให้คะแนน</h2>
              <p className="text-sm text-slate-600">
                ยังเป็น mock view — ส่วนนี้จะแสดงผลสรุปคะแนน + ปุ่ม trigger grading เมื่อ backend พร้อม
              </p>
              <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-6 text-center">
                <p className="text-sm text-slate-500">(Placeholder) กดปุ่มเพื่อเริ่ม grading</p>
                <Button className="mt-4" onClick={() => alert("ยังไม่เปิดใช้งาน")}>เริ่ม grading</Button>
              </div>
            </div>
          )}

          {activeTab === "info" && questions.length > 0 && (
            <div className="mt-8 rounded-lg border border-slate-200 bg-slate-50 p-4">
              <h3 className="text-base font-semibold text-slate-900">รายการคำถาม</h3>
              <div className="mt-3 space-y-3">
                {questions.map((q) => (
                  <div key={q.question_number} className="rounded-lg border border-slate-200 bg-white p-3">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="text-sm font-medium text-slate-700">คำถามที่ {q.question_number}</div>
                        <div className="mt-1 text-sm text-slate-600">{q.question_text}</div>
                      </div>
                      <div className="text-sm font-semibold text-slate-700">คะแนน: {q.max_score}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
