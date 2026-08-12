import { Box, Flex, Heading, Text } from '@chakra-ui/react';
import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  /** `soft` usa o quadrado amarelo-claro; `neutral` usa cinza. */
  tone?: 'soft' | 'neutral';
  children?: ReactNode;
}

/** Estado vazio centralizado, usado na conversa e no histórico. */
export function EmptyState({
  icon,
  title,
  description,
  action,
  tone = 'soft',
  children,
}: EmptyStateProps) {
  return (
    <Flex direction="column" align="center" textAlign="center" px="20px" width="100%">
      <Box
        display="grid"
        placeItems="center"
        width={tone === 'soft' ? '62px' : '58px'}
        height={tone === 'soft' ? '62px' : '58px'}
        borderRadius={tone === 'soft' ? '16px' : '15px'}
        borderWidth="1px"
        borderStyle="solid"
        bg={tone === 'soft' ? 'brand.tint' : 'background.subtle'}
        borderColor={tone === 'soft' ? 'brand.soft' : 'border.default'}
      >
        {icon}
      </Box>
      <Heading as="h2" mt={tone === 'soft' ? '22px' : '20px'} fontSize={tone === 'soft' ? '22px' : '20px'} fontWeight={600} color="text.primary">
        {title}
      </Heading>
      {description ? (
        <Text
          mt="10px"
          maxW={tone === 'soft' ? '52ch' : '44ch'}
          fontSize={{ base: '15px', md: '15.5px' }}
          lineHeight={1.6}
          color="text.muted"
        >
          {description}
        </Text>
      ) : null}
      {action ? <Box mt="24px">{action}</Box> : null}
      {children}
    </Flex>
  );
}
