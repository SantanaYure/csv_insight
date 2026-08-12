import type { Dataset } from './dataset';
import type { ChatMessage } from './message';
import type { QueryResult } from './query';

/** Envelope padrão esperado do backend FastAPI. */
export interface ApiEnvelope<T> {
  data: T;
  message?: string;
}

export interface ApiErrorPayload {
  detail?: string;
  message?: string;
  code?: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export type UploadDatasetResponse = ApiEnvelope<Dataset>;
export type GetDatasetResponse = ApiEnvelope<Dataset>;
export type AskQuestionResponse = ApiEnvelope<QueryResult>;
export type GetHistoryResponse = ApiEnvelope<ChatMessage[]>;

export interface AskQuestionRequest {
  question: string;
}
