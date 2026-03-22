"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import api from "@/lib/api";

interface GradingResult {
  id: string;
  question_number: number;
  llm_score: number;
  expert_score: number | null;
  max_score: number;
  reasoning: string;
  expert_feedback: string | null;
  status: "pending" | "approved" | "revised";
}

interface SubmissionDetail {
  student_name: string;
  student_code: string;
  grading_results: GradingResult[];
}

export default function ReviewPanelPage() {
  const { id, sid } = useParams() as { id?: string; sid?: string };
  const [detail, setDetail] = useState<SubmissionDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [override, setOverride] = useState<Record<string, { score: string; feedback: string }>>({});
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!sid) return;
    setLoading(true);
    setError(null);
    api
      .get(`/review/submissions/${sid}`)
      .then((resp) => {
        setDetail(resp.data);
        // Initialize override state
        const init: Record<string, { score: string; feedback: string }> = {};
        (resp.data.grading_results || []).forEach((r: GradingResult) => {
          init[r.id] = {
            score: r.expert_score?.toString() ?? "",
            feedback: r.expert_feedback ?? "",
          };
        });
        setOverride(init);
      })
      .catch(() => setError("ไม่สามารถโหลดข้อมูลได้"))
      .finally(() => setLoading(false));
  }, [sid]);

  const handleApprove = async (resultId: string) => {
    setActionLoading((prev) => ({ ...prev, [resultId]: true }));
    try {
      const resp = await api.put(`/review/results/${resultId}/approve`, {});
      setDetail((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          grading_results: prev.grading_results.map((r) =>
            r.id === resultId ? { ...r, ...resp.data } : r
          ),
        };
      });
    } catch {
      alert("Approve ล้มเหลว");
    } finally {
      setActionLoading((prev) => ({ ...prev, [resultId]: false }));
    }
  };

  const handleRevise = async (resultId: string) => {
    setActionLoading((prev) => ({ ...prev, [resultId]: true }));
    try {
      const { score, feedback } = override[resultId] || { score: "", feedback: "" };
      const expert_score = parseFloat(score);
      await api.put(`/review/results/${resultId}/revise`, {
        expert_score,
        expert_feedback: feedback,
      });
      setDetail((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          grading_results: prev.grading_results.map((r) =>
            r.id === resultId
              ? { ...r, expert_score, expert_feedback: feedback, status: "revised" }
              : r
          ),
        };
      });
    } catch {
      alert("Revise ล้มเหลว");
    } finally {
      setActionLoading((prev) => ({ ...prev, [resultId]: false }));
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">กำลังโหลด...</div>;
  }
  if (error) {
    return <div className="p-8 text-center text-red-500">{error}</div>;
  }
  if (!detail) {
    return null;
  }

  return (
    <div className="flex flex-col md:flex-row gap-4 w-full h-full">
      {/* Left: Student answers per question (placeholder) */}
      <div className="flex-1 min-w-0">
        <Card className="p-4 h-full">
          <h2 className="font-bold text-lg mb-2">Student Answers</h2>
          <div className="mb-2 text-muted-foreground">
            {detail.student_name} ({detail.student_code})
          </div>
          {/* TODO: Render actual student answers per question if available */}
          <div className="text-muted-foreground">(Student answers will appear here)</div>
        </Card>
      </div>
      {/* Right: LLM score + reasoning + expert override form per question */}
      <div className="flex-1 min-w-0">
        <Card className="p-4 h-full">
          <h2 className="font-bold text-lg mb-2">LLM Grading & Expert Review</h2>
          {detail.grading_results.length === 0 ? (
            <div className="text-muted-foreground">No grading results.</div>
          ) : (
            <div className="space-y-6">
              {detail.grading_results.map((r) => (
                <div key={r.id} className="border-b pb-4 mb-4 last:border-b-0 last:pb-0 last:mb-0">
                  <div className="font-medium mb-1">Question {r.question_number}</div>
                  <div className="mb-1 text-sm text-muted-foreground">Reasoning: {r.reasoning}</div>
                  <div className="mb-1 text-sm">
                    LLM Score: <span className="font-semibold">{r.llm_score} / {r.max_score}</span>
                  </div>
                  {r.expert_score !== null && (
                    <div className="mb-1 text-sm">
                      Expert Score: <span className="font-semibold">{r.expert_score} / {r.max_score}</span>
                    </div>
                  )}
                  {r.expert_feedback && (
                    <div className="mb-1 text-sm">Expert Feedback: {r.expert_feedback}</div>
                  )}
                  <form
                    className="mt-2 flex flex-col gap-2 md:flex-row md:items-end md:gap-4"
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleRevise(r.id);
                    }}
                  >
                    <div>
                      <Label htmlFor={`score-${r.id}`}>Override Score</Label>
                      <Input
                        id={`score-${r.id}`}
                        type="number"
                        min={0}
                        max={r.max_score}
                        value={override[r.id]?.score ?? ""}
                        onChange={(e) =>
                          setOverride((prev) => ({
                            ...prev,
                            [r.id]: { ...prev[r.id], score: e.target.value },
                          }))
                        }
                        className="w-24"
                        placeholder="Score"
                        disabled={actionLoading[r.id]}
                      />
                    </div>
                    <div className="flex-1">
                      <Label htmlFor={`feedback-${r.id}`}>Feedback</Label>
                      <Textarea
                        id={`feedback-${r.id}`}
                        value={override[r.id]?.feedback ?? ""}
                        onChange={(e) =>
                          setOverride((prev) => ({
                            ...prev,
                            [r.id]: { ...prev[r.id], feedback: e.target.value },
                          }))
                        }
                        placeholder="Enter feedback"
                        disabled={actionLoading[r.id]}
                      />
                    </div>
                    <div className="flex gap-2 mt-2 md:mt-0">
                      <Button
                        type="button"
                        variant="default"
                        onClick={() => handleApprove(r.id)}
                        disabled={actionLoading[r.id] || r.status === "approved"}
                      >
                        Approve
                      </Button>
                      <Button
                        type="submit"
                        variant="secondary"
                        disabled={actionLoading[r.id]}
                      >
                        Revise
                      </Button>
                    </div>
                  </form>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Status: {r.status}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
