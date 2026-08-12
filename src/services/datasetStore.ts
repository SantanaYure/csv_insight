import type { Dataset } from '../types/dataset';
import type { ChatMessage } from '../types/message';
import type { DataRow } from './ingestion/inferColumns';
import { buildSemantics, type DatasetSemantics } from './query/semantics';

interface StoredDataset {
  dataset: Dataset;
  rows: Record<string, DataRow[]>;
  history: ChatMessage[];
}

const STORAGE_KEY = 'csv-insight:datasets';
/** Acima disso o conjunto fica apenas em memória durante a sessão. */
const MAX_PERSISTED_BYTES = 4 * 1024 * 1024;
/**
 * Acima desta quantidade de linhas nem tentamos serializar: `JSON.stringify`
 * de centenas de milhares de registros é, ele mesmo, uma operação síncrona
 * pesada — sem este atalho, cada pergunta feita ao dataset (que chama
 * `addHistory` → `persist()`) travaria a aba por vários segundos só para
 * descobrir, no final, que o resultado nem cabe no sessionStorage.
 */
const MAX_PERSISTED_ROWS = 20_000;

const memory = new Map<string, StoredDataset>();
const semanticsCache = new Map<string, DatasetSemantics>();
let restored = false;

/**
 * Guarda os conjuntos carregados na sessão. Não existe nenhum dataset
 * pré-cadastrado: a aplicação começa vazia e só passa a ter dados depois de
 * um upload.
 */
export const datasetStore = {
  save(dataset: Dataset, rows: Record<string, DataRow[]>): void {
    restore();
    memory.set(dataset.id, { dataset, rows, history: [] });
    semanticsCache.delete(dataset.id);
    persist();
  },

  get(datasetId: string): StoredDataset | null {
    restore();
    return memory.get(datasetId) ?? null;
  },

  getDataset(datasetId: string): Dataset | null {
    return this.get(datasetId)?.dataset ?? null;
  },

  /** Último conjunto carregado, usado para retomar a navegação. */
  latest(): Dataset | null {
    restore();
    const entries = [...memory.values()];
    if (entries.length === 0) return null;
    return entries.sort(
      (a, b) => new Date(b.dataset.uploadedAt).getTime() - new Date(a.dataset.uploadedAt).getTime(),
    )[0].dataset;
  },

  has(datasetId: string): boolean {
    return this.get(datasetId) !== null;
  },

  semantics(datasetId: string): DatasetSemantics | null {
    const stored = this.get(datasetId);
    if (!stored) return null;

    const cached = semanticsCache.get(datasetId);
    if (cached) return cached;

    const built = buildSemantics(stored.dataset, stored.rows);
    semanticsCache.set(datasetId, built);
    return built;
  },

  history(datasetId: string): ChatMessage[] {
    return this.get(datasetId)?.history ?? [];
  },

  addHistory(datasetId: string, message: ChatMessage): void {
    const stored = this.get(datasetId);
    if (!stored) return;
    stored.history = [message, ...stored.history];
    persist();
  },

  removeHistory(datasetId: string, messageId: string): void {
    const stored = this.get(datasetId);
    if (!stored) return;
    stored.history = stored.history.filter((item) => item.id !== messageId);
    persist();
  },

  clear(): void {
    memory.clear();
    semanticsCache.clear();
    safeStorage()?.removeItem(STORAGE_KEY);
  },
};

function persist(): void {
  const storage = safeStorage();
  if (!storage) return;

  const entries = [...memory.values()];
  const totalRows = entries.reduce((total, entry) => total + entry.dataset.totalRows, 0);
  if (totalRows > MAX_PERSISTED_ROWS) {
    storage.removeItem(STORAGE_KEY);
    return;
  }

  try {
    const payload = JSON.stringify(entries);
    if (payload.length > MAX_PERSISTED_BYTES) {
      // Conjunto grande demais para o storage: mantemos só em memória.
      storage.removeItem(STORAGE_KEY);
      return;
    }
    storage.setItem(STORAGE_KEY, payload);
  } catch {
    // Quota excedida ou storage indisponível — a sessão continua em memória.
  }
}

function restore(): void {
  if (restored) return;
  restored = true;

  const storage = safeStorage();
  if (!storage) return;

  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return;

    const parsed = JSON.parse(raw) as StoredDataset[];
    parsed.forEach((entry) => {
      if (entry?.dataset?.id) {
        memory.set(entry.dataset.id, {
          dataset: entry.dataset,
          rows: entry.rows ?? {},
          history: entry.history ?? [],
        });
      }
    });
  } catch {
    storage.removeItem(STORAGE_KEY);
  }
}

function safeStorage(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.sessionStorage;
  } catch {
    return null;
  }
}
