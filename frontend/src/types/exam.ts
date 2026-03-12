import { UUID, ISODate } from './common';

// Exam Request types
export interface CreateExamRequest {
  title: string;
  subject: string;
  description?: string;
  total_questions: number;
}

export interface UpdateExamRequest {
  title?: string;
  subject?: string;
  description?: string;
}

// Question types
export interface CreateQuestionRequest {
  question_number: number;
  question_text: string;
  max_score: number;
}

export interface UpdateQuestionRequest {
  question_text?: string;
  max_score?: number;
}

export interface QuestionResponse {
  id: UUID;
  exam_id: UUID;
  question_number: number;
  question_text: string;
  max_score: number;
  created_at: ISODate;
}

// Exam Response types
export interface ExamResponse {
  id: UUID;
  title: string;
  subject: string;
  description: string | null;
  created_by: UUID;
  total_questions: number;
  created_at: ISODate;
  updated_at: ISODate;
}

export interface ExamDetailResponse extends ExamResponse {
  questions: QuestionResponse[];
}

export interface ExamListResponse {
  exams: ExamResponse[];
  total: number;
}
