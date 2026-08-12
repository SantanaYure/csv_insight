import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

import { colors } from './colors';
import { components } from './components';
import { semanticTokens } from './semanticTokens';
import { fonts, fontSizes, fontWeights, textStyles } from './typography';

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: false,
};

/** base < 480px · sm 480 · md 768 · lg 1024 · xl 1280. */
const breakpoints = {
  sm: '480px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

const radii = {
  none: '0',
  sm: '6px',
  md: '8px',
  lg: '10px',
  xl: '12px',
  '2xl': '14px',
  '3xl': '16px',
  full: '999px',
};

export const theme = extendTheme({
  config,
  breakpoints,
  colors,
  semanticTokens,
  fonts,
  fontSizes,
  fontWeights,
  textStyles,
  radii,
  components,
  styles: {
    global: {
      'html, body, #root': {
        height: '100%',
      },
      body: {
        bg: 'background.page',
        color: 'text.primary',
        fontFamily: 'body',
        WebkitFontSmoothing: 'antialiased',
      },
      '*::selection': {
        bg: 'brand.soft',
      },
      ':focus-visible': {
        outline: '2px solid',
        outlineColor: 'brand.primary',
        outlineOffset: '2px',
      },
      '@keyframes dotPulse': {
        '0%, 60%, 100%': { opacity: 0.22, transform: 'translateY(0)' },
        '30%': { opacity: 1, transform: 'translateY(-3px)' },
      },
      '@keyframes fadeUp': {
        from: { opacity: 0, transform: 'translateY(6px)' },
        to: { opacity: 1, transform: 'translateY(0)' },
      },
    },
  },
});

/** Gutter horizontal da página: 18px no mobile, 40px a partir do desktop. */
export const pageGutter = { base: '18px', md: '28px', lg: '40px' };

export default theme;
