import {
  Box,
  Flex,
  FormLabel,
  IconButton,
  Text,
  Textarea,
  VisuallyHidden,
} from '@chakra-ui/react';
import { ArrowRight } from 'lucide-react';
import { useEffect, useRef, type KeyboardEvent } from 'react';

interface QuestionInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isDisabled?: boolean;
}

/**
 * Caixa de pergunta fixa no rodapé da conversa.
 * Enter envia; Shift + Enter quebra a linha.
 */
export function QuestionInput({ value, onChange, onSubmit, isDisabled = false }: QuestionInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const element = textareaRef.current;
    if (!element) return;
    element.style.height = 'auto';
    element.style.height = `${Math.min(element.scrollHeight, 120)}px`;
  }, [value]);

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      onSubmit();
    }
  };

  return (
    <Box>
      <VisuallyHidden>
        <FormLabel htmlFor="question-input">Pergunta sobre os dados</FormLabel>
      </VisuallyHidden>

      <Flex
        align="flex-end"
        gap="10px"
        pl="16px"
        pr="10px"
        py="10px"
        bg="background.surface"
        borderWidth="1px"
        borderStyle="solid"
        borderColor="border.default"
        borderRadius="2xl"
        boxShadow="bubble"
        _focusWithin={{ borderColor: 'brand.primary' }}
      >
        <Textarea
          id="question-input"
          ref={textareaRef}
          variant="bare"
          rows={2}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Pergunte algo sobre seus dados..."
          maxH="120px"
          isDisabled={isDisabled}
        />
        <IconButton
          aria-label="Enviar pergunta"
          title="Enviar pergunta"
          variant="primary"
          width="44px"
          height="44px"
          minW="44px"
          flex="none"
          onClick={onSubmit}
          isDisabled={isDisabled || value.trim().length === 0}
          icon={<ArrowRight size={19} strokeWidth={2} />}
        />
      </Flex>

      <Text mt="9px" fontSize="12.5px" color="text.muted">
        <Text as="strong" fontWeight={600} color="text.secondary">
          Enter
        </Text>{' '}
        para enviar ·{' '}
        <Text as="strong" fontWeight={600} color="text.secondary">
          Shift + Enter
        </Text>{' '}
        para quebrar linha
      </Text>
    </Box>
  );
}
