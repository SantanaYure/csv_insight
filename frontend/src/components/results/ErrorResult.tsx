import { Box, Flex, Heading, Text } from '@chakra-ui/react';
import { Lightbulb } from 'lucide-react';

import type { ErrorQueryResult } from '../../types/query';

/** Resposta sem resultado: título, mensagem e sugestão de reformulação. */
export function ErrorResult({ result }: { result: ErrorQueryResult }) {
  return (
    <Box>
      <Heading as="h3" m={0} fontSize="16px" fontWeight={600} color="text.primary">
        {result.title}
      </Heading>
      <Text mt="9px" fontSize="15px" lineHeight={1.6} color="text.secondary">
        {result.message}
      </Text>

      {result.suggestion ? (
        <Flex
          gap="10px"
          mt="14px"
          px="15px"
          py="13px"
          borderRadius="lg"
          bg="brand.tint"
          borderWidth="1px"
          borderStyle="solid"
          borderColor="brand.soft"
        >
          <Box as="span" flex="none" mt="1px" color="brand.primaryHover">
            <Lightbulb size={17} strokeWidth={1.9} />
          </Box>
          <Text m={0} fontSize="14px" lineHeight={1.6} color="text.secondary">
            {result.suggestion}
          </Text>
        </Flex>
      ) : null}
    </Box>
  );
}
