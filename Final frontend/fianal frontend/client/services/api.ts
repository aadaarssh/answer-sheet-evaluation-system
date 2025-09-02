/**
 * API Service for AI Evaluation System Frontend
 * Handles all backend communication
 */

const API_BASE_URL = 'http://localhost:8000/api';

// Types matching backend models
export interface User {
  id: string;
  email: string;
  full_name: string;
  university: string;
  department: string;
  role: string;
  created_at: string;
  is_active: boolean;
}

export interface LoginRequest {
  username: string; // email
  password: string;
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  university: string;
  department: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface EvaluationScheme {
  id: string;
  scheme_name: string;
  subject: string;
  total_marks: number;
  passing_marks: number;
  questions: Question[];
  professor_id: string;
  created_at: string;
  updated_at: string;
  scheme_file?: SchemeFile;
}

export interface Question {
  question_number: number;
  max_marks: number;
  concepts: Concept[];
}

export interface Concept {
  concept: string;
  keywords: string[];
  weight: number;
  marks_allocation: number;
}

export interface SchemeFile {
  name: string;
  content: string;
  uploaded_at: string;
}

export interface ExamSession {
  id: string;
  session_name: string;
  professor_id: string;
  scheme_id: string;
  total_students: number;
  processed_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  estimated_completion?: string;
  completed_at?: string;
}

export interface AnswerScript {
  id: string;
  session_id: string;
  student_name: string;
  student_id: string;
  file_name: string;
  status: 'pending' | 'processing' | 'completed' | 'manual_review' | 'failed';
  created_at: string;
  processed_at?: string;
  ocr_confidence: number;
  processing_errors: string[];
}

export interface EvaluationResult {
  id: string;
  script_id: string;
  student_name: string;
  student_id: string;
  file_name: string;
  total_score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  question_scores: QuestionScore[];
  requires_manual_review: boolean;
  review_reasons: string[];
  evaluated_at: string;
  verification?: any;
  manual_override?: any;
}

export interface QuestionScore {
  question_number: number;
  score: number;
  max_score: number;
  concept_breakdown: ConceptEvaluation[];
  overall_confidence: number;
  needs_review: boolean;
  review_reasons: string[];
}

export interface ConceptEvaluation {
  concept: string;
  similarity_score: number;
  marks_awarded: number;
  max_marks: number;
  confidence: number;
  reasoning?: string;
}

// Auth token management
class TokenManager {
  private static TOKEN_KEY = 'auth_token';

  static setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  static getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  static removeToken(): void {
    localStorage.removeItem(this.TOKEN_KEY);
  }

  static isAuthenticated(): boolean {
    return this.getToken() !== null;
  }
}

// API Client class
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const token = TokenManager.getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return headers;
  }

  private getMultipartHeaders(): HeadersInit {
    const headers: HeadersInit = {};

    const token = TokenManager.getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      if (response.status === 401) {
        // Token expired or invalid
        TokenManager.removeToken();
        throw new Error('Authentication failed. Please login again.');
      }

      const errorData = await response.json().catch(() => ({ message: 'Network error' }));
      throw new Error(errorData.detail || errorData.message || 'API request failed');
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<T>(response);
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<T>(response);
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<T>(response);
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    return this.handleResponse<T>(response);
  }

  async postFormData<T>(endpoint: string, formData: FormData): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: this.getMultipartHeaders(),
      body: formData,
    });

    return this.handleResponse<T>(response);
  }
}

// Create API client instance
const apiClient = new ApiClient(API_BASE_URL);

// Auth API
export const authApi = {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    // FastAPI OAuth2PasswordRequestForm expects form data
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Login failed');
    }

    const authResponse = await response.json();
    TokenManager.setToken(authResponse.access_token);
    return authResponse;
  },

  async register(userData: RegisterRequest): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
  },

  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/auth/me');
  },

  async refreshToken(): Promise<AuthResponse> {
    const authResponse = await apiClient.post<AuthResponse>('/auth/refresh', {});
    TokenManager.setToken(authResponse.access_token);
    return authResponse;
  },

  logout(): void {
    TokenManager.removeToken();
  },

  isAuthenticated(): boolean {
    return TokenManager.isAuthenticated();
  }
};

// Schemes API
export const schemesApi = {
  async list(): Promise<EvaluationScheme[]> {
    return apiClient.get<EvaluationScheme[]>('/schemes/');
  },

  async get(schemeId: string): Promise<EvaluationScheme> {
    return apiClient.get<EvaluationScheme>(`/schemes/${schemeId}`);
  },

  async create(scheme: Omit<EvaluationScheme, 'id' | 'professor_id' | 'created_at' | 'updated_at'>): Promise<EvaluationScheme> {
    return apiClient.post<EvaluationScheme>('/schemes/', scheme);
  },

  async update(schemeId: string, updates: Partial<EvaluationScheme>): Promise<EvaluationScheme> {
    return apiClient.put<EvaluationScheme>(`/schemes/${schemeId}`, updates);
  },

  async delete(schemeId: string): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/schemes/${schemeId}`);
  },

  async uploadFile(schemeId: string, file: File): Promise<{ message: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.postFormData<{ message: string; filename: string }>(`/schemes/${schemeId}/upload-file`, formData);
  }
};

// Sessions API
export const sessionsApi = {
  async list(): Promise<ExamSession[]> {
    return apiClient.get<ExamSession[]>('/sessions/');
  },

  async get(sessionId: string): Promise<ExamSession> {
    return apiClient.get<ExamSession>(`/sessions/${sessionId}`);
  },

  async create(session: { session_name: string; scheme_id: string; total_students?: number }): Promise<ExamSession> {
    return apiClient.post<ExamSession>('/sessions/', session);
  },

  async getProgress(sessionId: string): Promise<any> {
    return apiClient.get<any>(`/sessions/${sessionId}/progress`);
  }
};

// Scripts API
export const scriptsApi = {
  async uploadBatch(sessionId: string, files: File[]): Promise<{
    message: string;
    uploaded_count: number;
    error_count: number;
    errors: string[];
    processing_mode: string;
    scripts: { id: string; filename: string }[];
  }> {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    
    files.forEach(file => {
      formData.append('files', file);
    });

    return apiClient.postFormData('/scripts/upload-batch', formData);
  },

  async uploadSingle(sessionId: string, studentName: string, studentId: string, file: File): Promise<{
    message: string;
    script_id: string;
    filename: string;
    processing_mode: string;
  }> {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('student_name', studentName);
    formData.append('student_id', studentId);
    formData.append('file', file);

    return apiClient.postFormData('/scripts/upload-single', formData);
  },

  async getSessionScripts(sessionId: string): Promise<{
    session_id: string;
    total_scripts: number;
    status_counts: Record<string, number>;
    scripts: Array<{
      id: string;
      student_name: string;
      student_id: string;
      filename: string;
      status: string;
      created_at: string;
      processed_at?: string;
      has_errors: boolean;
      ocr_confidence: number;
    }>;
  }> {
    return apiClient.get(`/scripts/${sessionId}/status`);
  },

  async getScriptDetails(scriptId: string): Promise<any> {
    return apiClient.get(`/scripts/${scriptId}/details`);
  }
};

// Evaluations API
export const evaluationsApi = {
  async processScript(scriptId: string): Promise<{
    message: string;
    script_id: string;
    total_score: number;
    max_score: number;
    percentage: number;
    needs_manual_review: boolean;
    ocr_confidence: number;
    verification_confidence: number;
  }> {
    return apiClient.post(`/evaluations/process-script/${scriptId}`, {});
  },

  async getSessionResults(sessionId: string, skip = 0, limit = 100): Promise<{
    session_id: string;
    session_name: string;
    total_results: number;
    results_shown: number;
    statistics: {
      total_evaluated: number;
      passed: number;
      failed: number;
      pass_rate: number;
      average_score: number;
    };
    results: EvaluationResult[];
  }> {
    return apiClient.get(`/evaluations/${sessionId}/results?skip=${skip}&limit=${limit}`);
  },

  async getDetailedEvaluation(scriptId: string): Promise<any> {
    return apiClient.get(`/evaluations/${scriptId}/detailed`);
  },

  async getReviewQueue(): Promise<{
    total_reviews: number;
    reviews: Array<{
      id: string;
      script_id: string;
      evaluation_id: string;
      student_name: string;
      student_id: string;
      session_name: string;
      subject: string;
      reason: string;
      priority: number;
      status: string;
      original_score: number;
      manual_score?: number;
      flagged_at: string;
      reviewed_at?: string;
      reviewer_notes: string;
    }>;
  }> {
    return apiClient.get('/evaluations/review-queue');
  },

  async submitManualReview(reviewId: string, reviewData: {
    manual_score: number;
    reviewer_notes: string;
    question_number?: number;
  }): Promise<{
    message: string;
    review_id: string;
    manual_score: number;
    original_score: number;
  }> {
    return apiClient.post(`/evaluations/${reviewId}/manual-review`, reviewData);
  }
};

// Health check
export const healthApi = {
  async check(): Promise<{ status: string; service: string; version: string }> {
    const response = await fetch('http://localhost:8000/health');
    if (!response.ok) {
      throw new Error('Backend is not available');
    }
    return response.json();
  }
};

// Export everything
export { TokenManager, ApiClient };
export default {
  auth: authApi,
  schemes: schemesApi,
  sessions: sessionsApi,
  scripts: scriptsApi,
  evaluations: evaluationsApi,
  health: healthApi
};