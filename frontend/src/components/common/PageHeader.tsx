import { Box, Flex, Heading, Text } from '@chakra-ui/react';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: ReactNode;
  description?: ReactNode;
  /** Elemento exibido à direita do título (badge de status). */
  badge?: ReactNode;
  /** Ações alinhadas à direita do bloco. */
  actions?: ReactNode;
  /** Conteúdo acima do título, como o breadcrumb da tela de upload. */
  eyebrow?: ReactNode;
  /** `h1` de página ou `h2` quando usado dentro de uma seção. */
  as?: 'h1' | 'h2';
  size?: 'h1' | 'h2';
}

/** Cabeçalho reutilizável de página: eyebrow, título, descrição e ações. */
export function PageHeader({
  title,
  description,
  badge,
  actions,
  eyebrow,
  as = 'h1',
  size = 'h1',
}: PageHeaderProps) {
  return (
    <Flex
      align="flex-start"
      justify="space-between"
      gap="20px"
      wrap="wrap"
      width="100%"
    >
      <Box minW={0}>
        {eyebrow}
        <Flex align="center" gap="12px" wrap="wrap" mt={eyebrow ? '18px' : 0}>
          <Heading as={as} size={size} m={0} color="text.primary">
            {title}
          </Heading>
          {badge}
        </Flex>
        {description ? (
          <Text mt="12px" fontSize={{ base: '15.5px', md: '16.5px' }} lineHeight={1.6} color="text.muted">
            {description}
          </Text>
        ) : null}
      </Box>
      {actions ? (
        <Flex gap="10px" wrap="wrap">
          {actions}
        </Flex>
      ) : null}
    </Flex>
  );
}
