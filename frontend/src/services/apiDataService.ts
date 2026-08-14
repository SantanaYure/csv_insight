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
import { apiRequest, uploadFile } from './http/apiClient';

/**
 * Implementação preparada para o backend FastAPI. Os endpoints seguem o
 * contrato documentado no README e o envelope `{ data }`.
 */
export const apiDataService: DataService = {
  async uploadDataset(file, options): Promise<Dataset> {
    const payload = await uploadFile<UploadDatasetResponse>('/datasets', file, options);

    return payload.data;
  },

  async getDataset(datasetId: string): Promise<Dataset> {
    const payload = await apiRequest<GetDatasetResponse>(
      `/datasets/${encodeURIComponent(datasetId)}`,
    );
    return payload.data;
  },

  async askQuestion(datasetId: string, question: string): Promise<QueryResult> {
    const payload = await apiRequest<AskQuestionResponse>(
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
    const payload = await apiRequest<GetHistoryResponse>(
      `/datasets/${encodeURIComponent(datasetId)}/history`,
    );
    return payload.data;
  },

  async deleteHistoryItem(datasetId: string, messageId: string): Promise<void> {
    await apiRequest<void>(
      `/datasets/${encodeURIComponent(datasetId)}/history/${encodeURIComponent(messageId)}`,
      { method: 'DELETE' },
    );
  },
};
