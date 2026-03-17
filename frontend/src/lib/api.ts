import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// ─── API Instance ─────────────────────────────────────────────────────────────
const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// ─── Token Management ─────────────────────────────────────────────────────────
let isRefreshing = false;
let failedQueue: Array<(token: string) => void> = [];

const processQueue = (token: string) => {
  failedQueue.forEach(callback => callback(token));
  failedQueue = [];
};

const refreshAccessToken = async (): Promise<string | null> => {
  try {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await axios.post(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/refresh`,
      { refresh_token: refreshToken }
    );

    const { access_token, refresh_token: newRefreshToken } = response.data;
    localStorage.setItem('authToken', access_token);
    if (newRefreshToken) {
      localStorage.setItem('refreshToken', newRefreshToken);
    }

    return access_token;
  } catch (error) {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/';
    return null;
  }
};

// ─── Request Interceptor ──────────────────────────────────────────────────────
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor ─────────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          failedQueue.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await refreshAccessToken();
        if (newToken) {
          processQueue(newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        }
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// ─── Exam API Functions ──────────────────────────────────────────────────────
import { ExamResponse, ExamListResponse, CreateExamRequest, UpdateExamRequest } from '@/types/exam';

export const examApi = {
  // Get all exams
  getExams: async (): Promise<ExamListResponse> => {
    const response = await api.get('/exams');
    return response.data;
  },

  // Get single exam
  getExam: async (examId: string): Promise<ExamResponse> => {
    const response = await api.get(`/exams/${examId}`);
    return response.data;
  },

  // Create exam
  createExam: async (data: CreateExamRequest): Promise<ExamResponse> => {
    const response = await api.post('/exams', data);
    return response.data;
  },

  // Update exam
  updateExam: async (examId: string, data: UpdateExamRequest): Promise<ExamResponse> => {
    const response = await api.put(`/exams/${examId}`, data);
    return response.data;
  },

  // Delete exam
  deleteExam: async (examId: string): Promise<void> => {
    await api.delete(`/exams/${examId}`);
  },
};