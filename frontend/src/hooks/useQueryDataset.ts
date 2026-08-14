import { useCallback, useEffect, useRef, useState } from 'react';

import { dataService } from '../services';
import type { ChatMessage } from '../types/message';
import { generateId } from '../utils/generateId';

interface UseQueryDatasetResult {
  messages: ChatMessage[];
  isAsking: boolean;
  ask: (question: string, options?: AskOptions) => Promise<void>;
  clear: () => void;
}

interface AskOptions {
  /** Remove a mensagem de erro que está sendo repetida antes de responder. */
  replaceMessageId?: string;
}

/**
 * Conduz a conversa da tela de consulta: adiciona a mensagem do usuário,
 * mantém o estado de carregamento e anexa a resposta retornada pelo serviço.
 */
export function useQueryDataset(datasetId: string | undefined): UseQueryDatasetResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const mounted = useRef(true);
  const askingRef = useRef(false);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const clear = useCallback(() => {
    setMessages([]);
  }, []);

  const ask = useCallback(
    async (question: string, options: AskOptions = {}) => {
      const trimmed = question.trim();
      if (!trimmed || !datasetId || askingRef.current) return;

      const startedAt = Date.now();
      askingRef.current = true;

      setMessages((current) => {
        const withoutRetriedError = options.replaceMessageId
          ? current.filter((message) => message.id !== options.replaceMessageId)
          : current;

        if (options.replaceMessageId) return withoutRetriedError;

        return [
          ...withoutRetriedError,
          {
            id: generateId('user'),
            role: 'user',
            content: trimmed,
            createdAt: new Date().toISOString(),
            status: 'complete',
          },
        ];
      });
      setIsAsking(true);

      try {
        const result = await dataService.askQuestion(datasetId, trimmed);
        if (!mounted.current) return;

        setMessages((current) => [
          ...current,
          {
            id: generateId('assistant'),
            role: 'assistant',
            content: trimmed,
            question: trimmed,
            createdAt: new Date().toISOString(),
            status: result.type === 'error' ? 'error' : 'complete',
            durationMs: Date.now() - startedAt,
            result,
          },
        ]);
      } catch (cause: unknown) {
        if (!mounted.current) return;

        setMessages((current) => [
          ...current,
          {
            id: generateId('assistant'),
            role: 'assistant',
            content: trimmed,
            question: trimmed,
            createdAt: new Date().toISOString(),
            status: 'error',
            durationMs: Date.now() - startedAt,
            result: {
              type: 'error',
              title: 'Não foi possível responder',
              message:
                cause instanceof Error
                  ? cause.message
                  : 'Ocorreu uma falha inesperada ao consultar os dados.',
              suggestion: 'Verifique a conexão e tente novamente em alguns instantes.',
            },
          },
        ]);
      } finally {
        askingRef.current = false;
        if (mounted.current) setIsAsking(false);
      }
    },
    [datasetId],
  );

  return { messages, isAsking, ask, clear };
}
