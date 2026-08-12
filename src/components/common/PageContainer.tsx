import { Box, type BoxProps } from '@chakra-ui/react';

import { pageGutter } from '../../theme';

interface PageContainerProps extends BoxProps {
  /** Largura máxima do conteúdo. O design usa 1320px nas seções públicas. */
  maxContentWidth?: BoxProps['maxW'];
  /** Remove o `margin: 0 auto` para conteúdos alinhados à esquerda. */
  align?: 'center' | 'start';
}

/** Aplica o gutter da página (18px mobile · 40px desktop) e a largura máxima. */
export function PageContainer({
  maxContentWidth = '1320px',
  align = 'center',
  children,
  ...rest
}: PageContainerProps) {
  return (
    <Box px={pageGutter} {...rest}>
      <Box maxW={maxContentWidth} mx={align === 'center' ? 'auto' : undefined}>
        {children}
      </Box>
    </Box>
  );
}
