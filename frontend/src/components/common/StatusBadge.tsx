import { Box, Flex, type FlexProps } from '@chakra-ui/react';
import type { ReactNode } from 'react';

export type StatusTone = 'brand' | 'soft' | 'neutral' | 'error';

interface StatusBadgeProps extends Omit<FlexProps, 'children'> {
  children: ReactNode;
  tone?: StatusTone;
  /** Exibe o ponto indicador à esquerda do texto (padrão do estado ativo). */
  withDot?: boolean;
  icon?: ReactNode;
}

const TONES = {
  brand: {
    bg: 'brand.primary',
    borderColor: 'brand.primary',
    color: 'brand.textOnPrimary',
    dot: '#111111',
  },
  soft: {
    bg: 'brand.tint',
    borderColor: 'brand.soft',
    color: 'text.secondary',
    dot: 'brand.primaryHover',
  },
  neutral: {
    bg: 'background.subtle',
    borderColor: 'border.default',
    color: 'text.secondary',
    dot: 'text.muted',
  },
  error: {
    bg: 'background.subtle',
    borderColor: 'feedback.error',
    color: 'feedback.error',
    dot: 'feedback.error',
  },
} as const;

/** Badge em pílula usado para status de dataset, tipos de resposta e filtros. */
export function StatusBadge({
  children,
  tone = 'brand',
  withDot = false,
  icon,
  ...rest
}: StatusBadgeProps) {
  const style = TONES[tone];

  return (
    <Flex
      as="span"
      display="inline-flex"
      align="center"
      gap="6px"
      height="28px"
      px="11px"
      borderRadius="full"
      borderWidth="1px"
      borderStyle="solid"
      bg={style.bg}
      borderColor={style.borderColor}
      color={style.color}
      fontSize="12.5px"
      fontWeight={600}
      whiteSpace="nowrap"
      {...rest}
    >
      {withDot ? (
        <Box as="span" width="5px" height="5px" borderRadius="full" bg={style.dot} flex="none" />
      ) : null}
      {icon}
      {children}
    </Flex>
  );
}
