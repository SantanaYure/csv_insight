import { Box } from '@chakra-ui/react';
import { MessageSquare } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { EmptyState } from '../common/EmptyState';
import { pageGutter } from '../../theme';
import { useQueryDataset } from '../../hooks/useQueryDataset';
import type { Dataset } from '../../types/dataset';
import { ChatContainer } from '../query/ChatContainer';
import { QuestionInput } from '../query/QuestionInput';
import { SuggestedQuestions } from '../query/SuggestedQuestions';

interface ChatPanelProps {
  dataset: Dataset;
  suggestions: string[];
  /** Pergunta vinda de uma sugestão ou do histórico, a ser preenchida uma vez. */
  pendingQuestion: string;
  onConsumePending: () => void;
}

/** Painel "Consulta": a conversa em linguagem natural (Interface B do desafio). */
export function ChatPanel({ dataset, suggestions, pendingQuestion, onConsumePending }: ChatPanelProps) {
  const [question, setQuestion] = useState('');
  const { messages, isAsking, ask } = useQueryDataset(dataset.id);

  useEffect(() => {
    if (pendingQuestion) {
      setQuestion(pendingQuestion);
      onConsumePending();
    }
  }, [pendingQuestion, onConsumePending]);

  const handleSubmit = useCallback(() => {
    if (!question.trim() || isAsking) return;
    const pending = question;
    setQuestion('');
    void ask(pending);
  }, [ask, isAsking, question]);

  const handleRetry = useCallback(
    (retryQuestion: string, messageId: string) => {
      if (isAsking) return;
      void ask(retryQuestion, { replaceMessageId: messageId });
    },
    [ask, isAsking],
  );

  return (
    <>
      <ChatContainer
        messages={messages}
        isAsking={isAsking}
        onRetry={handleRetry}
        emptyState={
          <EmptyState
            icon={
              <Box color="brand.primaryHover">
                <MessageSquare size={28} strokeWidth={1.7} />
              </Box>
            }
            title="Comece fazendo uma pergunta"
            description={`Perguntas sobre ${dataset.tables
              .map((table) => table.name)
              .join(', ')} — os valores são calculados sobre os arquivos que você enviou.`}
          >
            <SuggestedQuestions questions={suggestions} onSelect={setQuestion} />
          </EmptyState>
        }
      />

      <Box
        flex="none"
        px={pageGutter}
        pt="16px"
        pb={{ base: 'calc(16px + env(safe-area-inset-bottom))', md: '22px' }}
        borderTopWidth="1px"
        borderTopStyle="solid"
        borderColor="border.default"
        bg="background.page"
      >
        <Box maxW="820px" mx="auto">
          <QuestionInput
            value={question}
            onChange={setQuestion}
            onSubmit={handleSubmit}
            isDisabled={isAsking}
          />
        </Box>
      </Box>
    </>
  );
}
