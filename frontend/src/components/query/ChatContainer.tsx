import { Box, Flex } from '@chakra-ui/react';
import { useEffect, useRef } from 'react';

import type { ChatMessage } from '../../types/message';
import { ChatMessageItem } from './ChatMessage';
import { QueryLoadingMessage } from './QueryLoadingMessage';

interface ChatContainerProps {
  messages: ChatMessage[];
  isAsking: boolean;
  /** Conteúdo exibido quando ainda não há mensagens. */
  emptyState: React.ReactNode;
  onRetry?: (question: string, messageId: string) => void;
}

/** Área rolável da conversa, com rolagem automática para a última mensagem. */
export function ChatContainer({ messages, isAsking, emptyState, onRetry }: ChatContainerProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length, isAsking]);

  const isEmpty = messages.length === 0 && !isAsking;

  return (
    <Box flex="1" minH={0} overflowY="auto" px={{ base: '18px', md: '28px', lg: '40px' }} pt="28px" pb="8px">
      <Flex direction="column" gap="22px" maxW="820px" mx="auto" width="100%">
        {isEmpty ? (
          <Box py="48px">{emptyState}</Box>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessageItem key={message.id} message={message} onRetry={onRetry} />
            ))}
            {isAsking ? <QueryLoadingMessage /> : null}
          </>
        )}
        <Box ref={bottomRef} />
      </Flex>
    </Box>
  );
}
