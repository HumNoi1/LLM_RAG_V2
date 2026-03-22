"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

interface ResultRow {
  id: string;
  student_name: string;
  student_code: string;
  total_score: number;
  max_total_score: number;
  status: "graded" | "parsed" | "pending";
}

export default function ResultsTablePage() {
  const { id } = useParams() as { id?: string };
  const router = useRouter();
  const [results, setResults] = useState<ResultRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const handleExportCSV = async () => {
    if (!id) return;
    setExporting(true);
    try {
      const response = await api.get(`/review/exams/${id}/export`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `exam_${id}_results.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      alert("Export CSV ล้มเหลว");
    } finally {
      setExporting(false);
    }
  };

  const fetchResults = () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    api
      .get(`/review/exams/${id}/submissions`)
      .then((resp) => {
        setResults(resp.data.results ?? []);
      })
      .catch(() => {
        setError("ไม่สามารถโหลดผลคะแนนได้");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchResults();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleBulkApprove = async () => {
    if (!id) return;
    setBulkLoading(true);
    try {
      await api.post(`/review/exams/${id}/approve-all`, {});
      fetchResults();
    } catch {
      alert("Bulk approve ล้มเหลว");
    } finally {
      setBulkLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push(`/exams/${id}`)}>
            กลับหน้าข้อสอบ
          </Button>
          <h1 className="text-2xl font-semibold text-slate-900">ผลคะแนนนักศึกษา</h1>
        </div>
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <div className="mb-4 flex gap-2 justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportCSV}
              disabled={exporting || loading || results.length === 0}
            >
              {exporting ? "กำลังดาวน์โหลด..." : "Export CSV"}
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleBulkApprove}
              disabled={bulkLoading || loading || results.length === 0}
            >
              {bulkLoading ? "กำลังอนุมัติทั้งหมด..." : "Bulk Approve"}
            </Button>
          </div>
          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          ) : loading ? (
            <div className="text-center text-slate-500">กำลังโหลด...</div>
          ) : results.length === 0 ? (
            <div className="text-center text-slate-500">ยังไม่มีผลคะแนน</div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-xs font-semibold text-slate-600">
                  <tr>
                    <th className="px-4 py-3 text-left">ชื่อนักศึกษา</th>
                    <th className="px-4 py-3 text-left">รหัสนักศึกษา</th>
                    <th className="px-4 py-3 text-right">คะแนนรวม</th>
                    <th className="px-4 py-3 text-left">สถานะ</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {results.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-800">{row.student_name || "—"}</td>
                      <td className="px-4 py-3 text-slate-600">{row.student_code || "—"}</td>
                      <td className="px-4 py-3 text-right text-slate-800">
                        {row.total_score != null ? `${row.total_score} / ${row.max_total_score}` : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                            row.status === "graded"
                              ? "bg-emerald-100 text-emerald-700"
                              : row.status === "parsed"
                              ? "bg-blue-100 text-blue-700"
                              : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {row.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/exams/${id}/results/${row.id}`)}
                        >
                          Review
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
