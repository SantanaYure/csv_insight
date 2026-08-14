import { Box, Flex } from '@chakra-ui/react';
import { ArrowRight } from 'lucide-react';

interface SuggestedQuestionsProps {
  questions: string[];
  onSelect: (question: string) => void;
}

/** Lista de perguntas sugeridas exibida no estado vazio da conversa. */
export function SuggestedQuestions({ questions, onSelect }: SuggestedQuestionsProps) {
  return (
    <Flex direction="column" gap="8px" width="100%" maxW="520px" mt="28px">
      {questions.map((question) => (
        <Flex
          key={question}
          as="button"
          type="button"
          onClick={() => onSelect(question)}
          align="center"
          gap="11px"
          minH="48px"
          px="16px"
          py="10px"
          borderWidth="1px"
          borderStyle="solid"
          borderColor="border.default"
          borderRadius="lg"
          bg="background.surface"
          color="text.secondary"
          fontSize="14.5px"
          textAlign="left"
          cursor="pointer"
          _hover={{ borderColor: 'brand.primary', bg: 'brand.tint', color: 'text.primary' }}
        >
          <Box as="span" flex="none" color="brand.primaryHover" aria-hidden="true">
            <ArrowRight size={15} strokeWidth={2} />
          </Box>
          <Box as="span" flex="1" textAlign="left">
            {question}
          </Box>
        </Flex>
      ))}
    </Flex>
  );
}
