// Common types and enums used across the API
export type UserRole = 'teacher' | 'admin';
export type DocType = 'answer_key' | 'rubric' | 'course_material';
export type EmbeddingStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type GradingStatus = 'idle' | 'running' | 'completed' | 'failed';
export type GradingResultStatus = 'pending' | 'approved' | 'revised';
export type SubmissionStatus = 'uploaded' | 'parsed' | 'grading' | 'graded' | 'reviewed';

// Common type aliases
export type UUID = string; // "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export type ISODate = string; // "2026-03-06T12:00:00Z"

// Error response
export interface ApiErrorResponse {
  detail: string;
}
