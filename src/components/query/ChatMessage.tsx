import { Box, Flex, Text } from '@chakra-ui/react';
import { AlertCircle, BarChart3, Database, Info, Table2 } from 'lucide-react';
import type { ReactNode } from 'react';

import type { ChatMessage as ChatMessageModel } from '../../types/message';
import type { QueryResult } from '../../types/query';
import { QueryResultRenderer } from '../results/QueryResultRenderer';

/** Balão da pergunta do usuário, alinhado à direita. */
export function UserMessage({ content }: { content: string }) {
  return (
    <Flex justify="flex-end">
      <Text
        m={0}
        maxW={{ base: '88%', md: '76%' }}
        px="17px"
        py="13px"
        borderRadius="16px 16px 5px 16px"
        bg="chat.userBg"
        color="chat.userText"
        fontSize="15px"
        lineHeight={1.55}
      >
        {content}
      </Text>
    </Flex>
  );
}

/** Avatar quadrado do agente; muda de ícone conforme o tipo de resposta. */
function AssistantAvatar({ result }: { result?: QueryResult }) {
  const isError = result?.type === 'error';

  const icon: ReactNode = (() => {
    if (isError) return <AlertCircle size={17} strokeWidth={1.9} />;
    if (result?.type === 'table') return <Table2 size={17} strokeWidth={1.9} />;
    if (result?.type === 'chart' || result?.type === 'combined') {
      return <BarChart3 size={17} strokeWidth={2} />;
    }
    return <Database size={17} strokeWidth={1.9} />;
  })();

  return (
    <Box
      as="span"
      aria-hidden="true"
      flex="none"
      display="grid"
      placeItems="center"
      width="32px"
      height="32px"
      borderRadius="9px"
      bg={isError ? 'background.subtle' : 'brand.primary'}
      borderWidth={isError ? '1px' : 0}
      borderStyle="solid"
      borderColor="border.default"
      color={isError ? 'feedback.error' : '#111111'}
    >
      {icon}
    </Box>
  );
}

/** Envelope visual das respostas do agente. */
export function AssistantBubble({
  children,
  isError = false,
  result,
}: {
  children: ReactNode;
  isError?: boolean;
  result?: QueryResult;
}) {
  return (
    <Flex gap="12px">
      <AssistantAvatar result={result} />
      <Box
        flex="1"
        minW={0}
        px="20px"
        py="18px"
        bg="background.surface"
        borderWidth="1px"
        borderStyle="solid"
        borderColor="border.default"
        borderLeftWidth={isError ? '3px' : '1px'}
        borderLeftColor={isError ? 'feedback.error' : 'border.default'}
        borderRadius="16px"
        boxShadow="bubble"
      >
        {children}
      </Box>
    </Flex>
  );
}

/** Resposta completa do agente, incluindo o resultado renderizado. */
export function AssistantMessage({
  message,
  onRetry,
}: {
  message: ChatMessageModel;
  onRetry?: (question: string) => void;
}) {
  const isError = message.result?.type === 'error';

  return (
    <AssistantBubble isError={isError} result={message.result}>
      {message.result ? (
        <QueryResultRenderer
          result={message.result}
          durationMs={message.durationMs}
          onRetry={
            onRetry && message.question ? () => onRetry(message.question as string) : undefined
          }
        />
      ) : (
        <Text m={0} fontSize="15.5px" lineHeight={1.65} color="text.primary">
          {message.content}
        </Text>
      )}
    </AssistantBubble>
  );
}

/** Aviso do sistema exibido na área da conversa. */
export function SystemMessage({ content }: { content: string }) {
  return (
    <Flex
      role="status"
      align="center"
      gap="10px"
      px="16px"
      py="12px"
      borderRadius="12px"
      bg="background.subtle"
      borderWidth="1px"
      borderStyle="solid"
      borderColor="border.default"
    >
      <Box as="span" flex="none" color="text.muted">
        <Info size={16} strokeWidth={1.8} />
      </Box>
      <Text m={0} fontSize="14px" lineHeight={1.55} color="text.secondary">
        {content}
      </Text>
    </Flex>
  );
}

/** Escolhe o componente conforme o papel da mensagem. */
export function ChatMessageItem({
  message,
  onRetry,
}: {
  message: ChatMessageModel;
  onRetry?: (question: string) => void;
}) {
  if (message.role === 'user') return <UserMessage content={message.content} />;
  if (message.role === 'system') return <SystemMessage content={message.content} />;
  return <AssistantMessage message={message} onRetry={onRetry} />;
}
