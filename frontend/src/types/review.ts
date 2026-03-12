import { UUID, ISODate, SubmissionStatus } from './common';
import { GradingResultResponse } from './grading';

// Review Request types
export interface ApproveGradingResultRequest {
  // empty object
}

export interface ReviseGradingResultRequest {
  expert_score: number;
  expert_feedback: string;
}

export interface BulkApproveRequest {
  // empty object
}

// Review Response types
export interface SubmissionDetailResponse {
  id: UUID;
  exam_id: UUID;
  student_name: string;
  student_code: string;
  status: SubmissionStatus;
  grading_results: GradingResultResponse[];
  total_score: number | null;
  max_total_score: number;
  created_at: ISODate;
}

export interface BulkApproveResponse {
  approved_count: number;
  message: string;
}

export interface ExportResponse {
  // Response will be CSV file with headers:
  // student_code, student_name, q1_score, q1_max, q2_score, q2_max, ..., total_score, max_total, status
}
