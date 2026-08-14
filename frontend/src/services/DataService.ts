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

export interface UploadDatasetOptions {
  /** Cancela a leitura local ou a requisição HTTP em andamento. */
  signal?: AbortSignal;
  /** Percentual de bytes enviados ao backend. */
  onUploadProgress?: (percentage: number) => void;
  /** Progresso de leitura das tabelas, quando disponível. */
  onProcessingProgress?: (progress: UploadProgress) => void;
}

/**
 * Contrato único de acesso a dados. Nenhum componente deve chamar `fetch`
 * diretamente: sempre passe por uma implementação desta interface.
 */
export interface DataService {
  uploadDataset(file: File, options?: UploadDatasetOptions): Promise<Dataset>;

  getDataset(datasetId: string): Promise<Dataset>;

  askQuestion(datasetId: string, question: string): Promise<QueryResult>;

  getHistory(datasetId: string): Promise<ChatMessage[]>;

  deleteHistoryItem(datasetId: string, messageId: string): Promise<void>;
}
