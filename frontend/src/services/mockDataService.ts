import type { Dataset } from '../types/dataset';
import type { ChatMessage } from '../types/message';
import type { QueryResult } from '../types/query';
import { generateId } from '../utils/generateId';
import type { DataService } from './DataService';
import { datasetStore } from './datasetStore';
import { readZipDataset } from './ingestion/readZipDataset';
import { answerQuestion } from './query/queryEngine';

const MIN_ANSWER_DELAY = 900;
const MAX_ANSWER_DELAY = 1_500;

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function randomDelay(min: number, max: number): number {
  return Math.round(min + Math.random() * (max - min));
}

/**
 * Implementação local: o ZIP é lido no navegador e as respostas são
 * calculadas sobre os dados carregados. Não há conjunto de demonstração —
 * a aplicação começa vazia.
 */
export const mockDataService: DataService = {
  async uploadDataset(file, options): Promise<Dataset> {
    if (options?.signal?.aborted) throw new DOMException('Upload cancelado.', 'AbortError');
    options?.onUploadProgress?.(100);
    const { dataset, rows } = await readZipDataset(file, options?.onProcessingProgress);
    if (options?.signal?.aborted) throw new DOMException('Upload cancelado.', 'AbortError');
    datasetStore.save(dataset, rows);
    return dataset;
  },

  async getDataset(datasetId: string): Promise<Dataset> {
    await delay(120);

    const dataset = datasetStore.getDataset(datasetId);
    if (!dataset) {
      throw new Error(
        'Nenhum conjunto de dados carregado nesta sessão. Envie um CSV ou ZIP para começar.',
      );
    }
    return dataset;
  },

  async askQuestion(datasetId: string, question: string): Promise<QueryResult> {
    const duration = randomDelay(MIN_ANSWER_DELAY, MAX_ANSWER_DELAY);
    await delay(duration);

    const semantics = datasetStore.semantics(datasetId);
    if (!semantics) {
      throw new Error('O conjunto de dados não está mais disponível. Envie o arquivo novamente.');
    }

    const result = answerQuestion(semantics, question);

    datasetStore.addHistory(datasetId, {
      id: generateId('history'),
      role: 'assistant',
      content: question,
      question,
      createdAt: new Date().toISOString(),
      status: result.type === 'error' ? 'error' : 'complete',
      durationMs: duration,
      result,
    });

    return result;
  },

  async getHistory(datasetId: string): Promise<ChatMessage[]> {
    await delay(120);
    return [...datasetStore.history(datasetId)].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    );
  },

  async deleteHistoryItem(datasetId: string, messageId: string): Promise<void> {
    await delay(120);
    datasetStore.removeHistory(datasetId, messageId);
  },
};
