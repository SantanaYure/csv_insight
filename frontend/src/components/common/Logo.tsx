import { Box, Flex, Text } from '@chakra-ui/react';

interface LogoProps {
  /** Tamanho do quadrado da marca. */
  size?: number;
  /** Tamanho do texto ao lado da marca. */
  fontSize?: string;
  /** Exibe apenas a marca, sem o nome. */
  markOnly?: boolean;
}

/** Marca do CSV Insight: base de dados combinada com um painel de gráfico. */
export function LogoMark({ size = 34 }: { size?: number }) {
  const icon = Math.round(size * 0.56);

  return (
    <Box
      as="span"
      display="grid"
      placeItems="center"
      width={`${size}px`}
      height={`${size}px`}
      borderRadius={size >= 32 ? '9px' : '8px'}
      bg="brand.primary"
      flex="none"
    >
      <svg
        width={icon}
        height={icon}
        viewBox="0 0 24 24"
        fill="none"
        stroke="#111111"
        strokeWidth="1.8"
        strokeLinecap="round"
        aria-hidden="true"
        focusable="false"
      >
        <ellipse cx="12" cy="6" rx="7" ry="3" />
        <path d="M5 6v6c0 1.66 3.13 3 7 3" />
        <path d="M19 6v4" />
        <rect x="12" y="12" width="10" height="8" rx="2.5" />
        <path d="M15 20l-1.5 2.5V20" />
      </svg>
    </Box>
  );
}

export function Logo({ size = 34, fontSize = '17px', markOnly = false }: LogoProps) {
  return (
    <Flex align="center" gap={markOnly ? 0 : '10px'}>
      <LogoMark size={size} />
      {!markOnly ? (
        <Text
          as="span"
          fontSize={fontSize}
          fontWeight={700}
          letterSpacing="-0.01em"
          color="text.primary"
        >
          CSV Insight
        </Text>
      ) : null}
    </Flex>
  );
}
