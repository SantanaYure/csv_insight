import { ApiError } from '../../types/api';
import type { UploadDatasetOptions } from '../DataService';

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace(/\/$/, '');

interface RequestOptions {
  method?: 'GET' | 'POST' | 'DELETE';
  body?: BodyInit;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      method: options.method ?? 'GET',
      body: options.body,
      headers: options.headers,
      signal: options.signal,
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause;
    throw new ApiError(
      'Não foi possível conectar ao backend. Confirme que a API está em execução e tente novamente.',
      0,
      'NETWORK_ERROR',
    );
  }

  if (!response.ok) {
    throw new ApiError(await readFetchError(response), response.status);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** XMLHttpRequest é usado somente no upload porque `fetch` não informa o progresso enviado. */
export function uploadFile<T>(
  path: string,
  file: File,
  options: UploadDatasetOptions = {},
): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file, file.name);

    const rejectAsAborted = () => reject(new DOMException('Upload cancelado.', 'AbortError'));
    const abortRequest = () => xhr.abort();
    const cleanup = () => options.signal?.removeEventListener('abort', abortRequest);

    if (options.signal?.aborted) {
      rejectAsAborted();
      return;
    }

    xhr.open('POST', `${API_URL}${path}`);
    xhr.responseType = 'json';

    xhr.upload.addEventListener('progress', (event) => {
      if (!event.lengthComputable) return;
      options.onUploadProgress?.(Math.min(100, Math.round((event.loaded / event.total) * 100)));
    });

    xhr.addEventListener('load', () => {
      cleanup();
      if (xhr.status >= 200 && xhr.status < 300) {
        options.onUploadProgress?.(100);
        resolve(xhr.response as T);
        return;
      }
      reject(new ApiError(readXhrError(xhr), xhr.status));
    });
    xhr.addEventListener('error', () => {
      cleanup();
      reject(
        new ApiError(
          'Não foi possível conectar ao backend. Confirme que a API está em execução e tente novamente.',
          0,
          'NETWORK_ERROR',
        ),
      );
    });
    xhr.addEventListener('abort', () => {
      cleanup();
      rejectAsAborted();
    });

    options.signal?.addEventListener('abort', abortRequest, { once: true });
    xhr.send(formData);
  });
}

async function readFetchError(response: Response): Promise<string> {
  try {
    return errorMessage((await response.json()) as unknown, response.status);
  } catch {
    return `Falha na requisição (${response.status}).`;
  }
}

function readXhrError(xhr: XMLHttpRequest): string {
  if (xhr.response) return errorMessage(xhr.response, xhr.status);
  return `Falha no upload (${xhr.status || 'sem resposta do servidor'}).`;
}

function errorMessage(payload: unknown, status: number): string {
  if (typeof payload === 'object' && payload !== null) {
    const error = payload as { detail?: unknown; message?: unknown };
    if (typeof error.detail === 'string') return error.detail;
    if (typeof error.message === 'string') return error.message;
  }
  return `Falha na requisição (${status}).`;
}
