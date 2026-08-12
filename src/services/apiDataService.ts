import { ApiError } from '../types/api';
import type {
  AskQuestionResponse,
  GetDatasetResponse,
  GetHistoryResponse,
  UploadDatasetResponse,
} from '../types/api';
import type { Dataset } from '../types/dataset';
import type { ChatMessage } from '../types/message';
import type { QueryResult } from '../types/query';
import type { DataService } from './DataService';

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace(/\/$/, '');

interface RequestOptions {
  method?: 'GET' | 'POST' | 'DELETE';
  body?: BodyInit;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: options.method ?? 'GET',
    body: options.body,
    headers: options.headers,
    signal: options.signal,
  });

  if (!response.ok) {
    throw new ApiError(await readErrorMessage(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string; message?: string };
    return payload.detail ?? payload.message ?? `Falha na requisição (${response.status}).`;
  } catch {
    return `Falha na requisição (${response.status}).`;
  }
}

/**
 * Implementação preparada para o backend FastAPI. Os endpoints seguem o
 * contrato documentado no README e o envelope `{ data }`.
 */
export const apiDataService: DataService = {
  // O backend real processa o arquivo do lado do servidor; não há progresso
  // de leitura para reportar aqui (a assinatura aceita o callback apenas
  // para manter paridade com `DataService`).
  async uploadDataset(file: File): Promise<Dataset> {
    const formData = new FormData();
    formData.append('file', file);

    const payload = await request<UploadDatasetResponse>('/datasets', {
      method: 'POST',
      body: formData,
    });

    return payload.data;
  },

  async getDataset(datasetId: string): Promise<Dataset> {
    const payload = await request<GetDatasetResponse>(
      `/datasets/${encodeURIComponent(datasetId)}`,
    );
    return payload.data;
  },

  async askQuestion(datasetId: string, question: string): Promise<QueryResult> {
    const payload = await request<AskQuestionResponse>(
      `/datasets/${encodeURIComponent(datasetId)}/questions`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      },
    );
    return payload.data;
  },

  async getHistory(datasetId: string): Promise<ChatMessage[]> {
    const payload = await request<GetHistoryResponse>(
      `/datasets/${encodeURIComponent(datasetId)}/history`,
    );
    return payload.data;
  },

  async deleteHistoryItem(datasetId: string, messageId: string): Promise<void> {
    await request<void>(
      `/datasets/${encodeURIComponent(datasetId)}/history/${encodeURIComponent(messageId)}`,
      { method: 'DELETE' },
    );
  },
};
