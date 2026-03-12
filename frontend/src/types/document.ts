import { UUID, ISODate, DocType, EmbeddingStatus, SubmissionStatus } from './common';

// Document Response types
export interface DocumentResponse {
  id: UUID;
  exam_id: UUID;
  doc_type: DocType;
  original_filename: string;
  embedding_status: EmbeddingStatus;
  chunk_count: number | null;
  created_at: ISODate;
}

export interface DocumentUploadResponse {
  message: string;
  document: DocumentResponse;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
  total: number;
}

// Submission types
export interface SubmissionSummary {
  id: UUID;
  student_name: string;
  student_code: string;
  status: SubmissionStatus;
  total_score: number | null;
  max_total_score: number;
  graded_questions: number;
  total_questions: number;
}

export interface SubmissionListResponse {
  submissions: SubmissionSummary[];
  total: number;
}
