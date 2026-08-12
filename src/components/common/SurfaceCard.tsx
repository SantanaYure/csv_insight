import { Box, type BoxProps } from '@chakra-ui/react';
import { forwardRef } from 'react';

export interface SurfaceCardProps extends BoxProps {
  /** `soft` usa o fundo amarelo-claro reservado a destaques. */
  tone?: 'default' | 'soft' | 'muted';
  /** Aplica a sombra discreta de card. */
  elevated?: boolean;
}

/**
 * Card base do design: raio 14px, borda de 1px e sombra opcional em uma camada.
 */
export const SurfaceCard = forwardRef<HTMLDivElement, SurfaceCardProps>(function SurfaceCard(
  { tone = 'default', elevated = true, children, ...rest },
  ref,
) {
  const tones = {
    default: { bg: 'background.surface', borderColor: 'border.default' },
    soft: { bg: 'brand.tint', borderColor: 'brand.soft' },
    muted: { bg: 'background.page', borderColor: 'border.default' },
  } as const;

  return (
    <Box
      ref={ref}
      borderWidth="1px"
      borderStyle="solid"
      borderRadius="2xl"
      boxShadow={elevated && tone === 'default' ? 'card' : undefined}
      {...tones[tone]}
      {...rest}
    >
      {children}
    </Box>
  );
});
