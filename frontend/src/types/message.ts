import type { QueryResult } from './query';

export type ChatRole = 'user' | 'assistant' | 'system';

export type ChatMessageStatus = 'sending' | 'processing' | 'complete' | 'error';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  status?: ChatMessageStatus;
  result?: QueryResult;
  /** Pergunta que originou a resposta, usada no histórico. */
  question?: string;
  /** Duração da consulta em milissegundos, exibida no rodapé da resposta. */
  durationMs?: number;
}
