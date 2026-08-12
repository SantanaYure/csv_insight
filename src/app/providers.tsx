import { ChakraProvider, ColorModeScript } from '@chakra-ui/react';
import type { ReactNode } from 'react';

import { theme } from '../theme';

/** Provedores globais da aplicação. */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <>
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      <ChakraProvider theme={theme}>{children}</ChakraProvider>
    </>
  );
}
