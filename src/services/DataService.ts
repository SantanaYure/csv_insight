import type { Dataset } from '../types/dataset';
import type { ChatMessage } from '../types/message';
import type { QueryResult } from '../types/query';

/** Progresso reportado durante a leitura de um dataset grande. */
export interface UploadProgress {
  fileName: string;
  rowCount: number;
  tableIndex: number;
  tableCount: number;
}

/**
 * Contrato único de acesso a dados. Nenhum componente deve chamar `fetch`
 * diretamente: sempre passe por uma implementação desta interface.
 */
export interface DataService {
  uploadDataset(file: File, onProgress?: (progress: UploadProgress) => void): Promise<Dataset>;

  getDataset(datasetId: string): Promise<Dataset>;

  askQuestion(datasetId: string, question: string): Promise<QueryResult>;

  getHistory(datasetId: string): Promise<ChatMessage[]>;

  deleteHistoryItem(datasetId: string, messageId: string): Promise<void>;
}
