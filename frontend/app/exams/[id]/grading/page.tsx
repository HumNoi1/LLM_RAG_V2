import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { Button } from "../../../../src/components/ui/button";
import { Progress } from "../../../../src/components/ui/progress";
import axios from "../../../../src/lib/api";
import type { GradingProgressResponse } from "../../../../src/types/grading";
import type { GradingStatus } from "../../../../src/types/common";

export default function GradingPage() {
  const router = useRouter();
  const examId = router.query?.id as string;
  const [status, setStatus] = useState<GradingProgressResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const pollStatus = async () => {
    try {
      const res = await axios.get(`/grading/status/${examId}`);
      setStatus(res.data);
      if (res.data.status === "completed") {
        setLoading(false);
      }
    } catch (err) {
      // handle error
    }
  };

  useEffect(() => {
    if (loading) {
      const interval = setInterval(pollStatus, 2000);
      pollStatus();
      return () => clearInterval(interval);
    }
  }, [loading, examId]);

  const handleTriggerGrading = async () => {
    setLoading(true);
    try {
      await axios.post(`/grading/start`, { exam_id: examId });
      pollStatus();
    } catch (err) {
      setLoading(false);
      // handle error
    }
  };

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Grading</h2>
      <Button onClick={handleTriggerGrading} disabled={loading || status?.status === "running"}>
        {loading || status?.status === "running" ? "Grading in progress..." : "Trigger Grading"}
      </Button>
      {(loading || status?.status === "running") && (
        <div className="mt-6">
          <Progress value={status?.progress_percent ?? 0} />
          <div className="mt-2 text-sm">{status?.progress_percent ?? 0}% complete</div>
        </div>
      )}
      {status?.status === "completed" && (
        <div className="mt-4 text-green-600">Grading completed!</div>
      )}
    </div>
  );
}
