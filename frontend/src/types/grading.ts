import { UUID, ISODate, GradingStatus, GradingResultStatus } from './common';

// Grading Request types
export interface StartGradingRequest {
  exam_id: UUID;
}

// Grading Response types
export interface GradingProgressResponse {
  exam_id: UUID;
  status: GradingStatus;
  total_submissions: number;
  completed: number;
  failed: number;
  progress_percent: number;
}

export interface GradingResultResponse {
  id: UUID;
  submission_id: UUID;
  question_id: UUID;
  question_number: number;
  llm_score: number;
  expert_score: number | null;
  max_score: number;
  reasoning: string;
  expert_feedback: string | null;
  status: GradingResultStatus;
  created_at: ISODate;
}
