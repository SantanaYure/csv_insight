import type { ComponentStyleConfig } from '@chakra-ui/react';

import { textStyles } from './typography';

type StyleConfig = ComponentStyleConfig;

/**
 * Overrides de componentes do Chakra alinhados ao design:
 * botões e inputs com 44px de altura mínima e raio 10px, cards com raio 14px
 * e badges com raio total.
 */
const Button: StyleConfig = {
  baseStyle: {
    borderRadius: '10px',
    fontWeight: 600,
    minH: '44px',
    _focusVisible: {
      boxShadow: 'none',
      outline: '2px solid',
      outlineColor: 'brand.primary',
      outlineOffset: '2px',
    },
  },
  sizes: {
    sm: { fontSize: '14px', minH: '40px', px: '14px' },
    md: { fontSize: '15px', minH: '44px', px: '18px' },
    lg: { fontSize: '16px', minH: '48px', px: '22px' },
  },
  variants: {
    primary: {
      bg: 'brand.primary',
      border: '1px solid',
      borderColor: 'brand.primaryHover',
      color: 'brand.textOnPrimary',
      _hover: {
        bg: 'brand.primaryHover',
        _disabled: { bg: 'background.subtle' },
      },
      _active: { bg: 'brand.primaryActive' },
      _disabled: {
        bg: 'background.subtle',
        borderColor: 'border.default',
        color: 'text.muted',
        cursor: 'not-allowed',
        opacity: 1,
      },
    },
    secondary: {
      bg: 'background.surface',
      border: '1px solid',
      borderColor: 'border.contrast',
      color: 'text.primary',
      _hover: {
        bg: 'background.subtle',
        _disabled: { bg: 'background.subtle' },
      },
      _active: { bg: 'background.subtle' },
      _disabled: {
        bg: 'background.subtle',
        borderColor: 'border.default',
        color: 'text.muted',
        cursor: 'not-allowed',
        opacity: 1,
      },
    },
    subtle: {
      bg: 'transparent',
      border: '1px solid',
      borderColor: 'border.default',
      color: 'text.secondary',
      fontWeight: 500,
      _hover: { bg: 'background.subtle', color: 'text.primary' },
    },
    ghost: {
      bg: 'transparent',
      border: '1px solid transparent',
      color: 'text.secondary',
      fontWeight: 500,
      _hover: { bg: 'background.subtle', color: 'text.primary' },
    },
    icon: {
      bg: 'transparent',
      border: 0,
      borderRadius: '8px',
      color: 'text.muted',
      minH: 'auto',
      _hover: { bg: 'background.subtle', color: 'text.primary' },
    },
  },
  defaultProps: { variant: 'secondary' },
};

const inputField = {
  minH: '44px',
  height: '44px',
  borderRadius: '10px',
  bg: 'background.surface',
  border: '1px solid',
  borderColor: 'border.default',
  color: 'text.primary',
  // 16px no mobile evita o zoom automático do iOS Safari ao focar o campo.
  fontSize: { base: '16px', md: '15px' },
  _placeholder: { color: 'text.muted' },
  _hover: { borderColor: 'border.strong' },
  _focusVisible: {
    borderColor: 'brand.primary',
    boxShadow: 'none',
    outline: 'none',
  },
  _invalid: {
    borderColor: 'feedback.error',
    boxShadow: 'none',
  },
};

const Input: StyleConfig = {
  baseStyle: { field: inputField },
  sizes: { md: { field: { ...inputField, px: '14px' } } },
  variants: { outline: { field: inputField } },
  defaultProps: { variant: 'outline', focusBorderColor: 'brand.primary' },
};

const Textarea: StyleConfig = {
  baseStyle: {
    ...inputField,
    height: 'auto',
    py: '10px',
    px: '14px',
    lineHeight: 1.5,
  },
  variants: {
    outline: { ...inputField, height: 'auto', py: '10px', px: '14px' },
    /** Textarea sem moldura, usado dentro da caixa de pergunta. */
    bare: {
      border: 0,
      bg: 'transparent',
      minH: '44px',
      height: 'auto',
      px: 0,
      py: '10px',
      fontSize: { base: '16px', md: '15.5px' },
      lineHeight: 1.5,
      color: 'text.primary',
      resize: 'none',
      _placeholder: { color: 'text.muted' },
      _focusVisible: { boxShadow: 'none', outline: 'none' },
    },
  },
  defaultProps: { variant: 'outline', focusBorderColor: 'brand.primary' },
};

/**
 * As escalas do design entram como `sizes` do Heading. Isso é necessário
 * porque a variante de tamanho do Chakra tem precedência sobre `textStyle`.
 */
const Heading: StyleConfig = {
  baseStyle: {
    color: 'text.primary',
    fontWeight: 700,
  },
  sizes: {
    display: textStyles.display,
    h1: textStyles.h1,
    h2: textStyles.h2,
    h3: textStyles.h3,
    subtitle: textStyles.subtitle,
  },
  defaultProps: { size: 'h3' },
};

const Link: StyleConfig = {
  baseStyle: {
    color: 'brand.primaryActive',
    _hover: { color: 'brand.primaryHover', textDecoration: 'underline' },
    _focusVisible: {
      boxShadow: 'none',
      outline: '2px solid',
      outlineColor: 'brand.primary',
      outlineOffset: '2px',
    },
  },
};

const Tabs: StyleConfig = {
  variants: {
    line: {
      tablist: {
        gap: '24px',
        borderBottom: '1px solid',
        borderColor: 'border.default',
      },
      tab: {
        px: '2px',
        pb: '13px',
        pt: 0,
        fontSize: '15px',
        fontWeight: 600,
        color: 'text.muted',
        borderBottom: '2px solid transparent',
        marginBottom: '-1px',
        whiteSpace: 'nowrap',
        _selected: { color: 'text.primary', borderColor: 'text.primary' },
        _focusVisible: {
          boxShadow: 'none',
          outline: '2px solid',
          outlineColor: 'brand.primary',
          outlineOffset: '2px',
        },
      },
      tabpanel: { px: 0, pb: 0, pt: '28px' },
    },
  },
  defaultProps: { variant: 'line' },
};

const Modal: StyleConfig = {
  baseStyle: {
    overlay: { bg: 'rgba(17,17,17,.55)' },
    dialog: {
      bg: 'background.surface',
      border: '1px solid',
      borderColor: 'border.default',
      borderRadius: '16px',
      boxShadow: 'dialog',
      p: '28px',
    },
    header: { p: 0, fontSize: '20px', fontWeight: 600, color: 'text.primary' },
    body: { p: 0, mt: '12px' },
    footer: { p: 0, mt: '26px', gap: '10px' },
  },
};

const Drawer: StyleConfig = {
  baseStyle: {
    overlay: { bg: 'rgba(17,17,17,.5)' },
    dialog: {
      bg: 'background.surface',
      borderRight: '1px solid',
      borderColor: 'border.default',
    },
  },
};

const Progress: StyleConfig = {
  baseStyle: {
    track: { bg: 'background.subtle', borderRadius: '999px' },
    filledTrack: { bg: 'brand.primary', borderRadius: '999px' },
  },
};

const Table: StyleConfig = {
  baseStyle: {
    th: {
      fontSize: '11.5px',
      fontWeight: 600,
      letterSpacing: '0.06em',
      textTransform: 'uppercase',
      color: 'text.muted',
      bg: 'background.subtle',
      borderBottom: 0,
    },
    td: {
      borderTop: '1px solid',
      borderColor: 'border.default',
      borderBottom: 0,
      color: 'text.primary',
    },
  },
  variants: {
    insight: {
      th: { py: '11px', px: '14px' },
      td: { py: '11px', px: '14px' },
    },
  },
  defaultProps: { variant: 'insight' },
};

const Tooltip: StyleConfig = {
  baseStyle: {
    bg: 'background.inverse',
    color: '#FFFFFF',
    borderRadius: '8px',
    fontSize: '12.5px',
    px: '10px',
    py: '6px',
  },
};

const Spinner: StyleConfig = {
  baseStyle: {
    borderColor: 'border.default',
    borderBottomColor: 'brand.primaryHover',
    borderLeftColor: 'brand.primaryHover',
  },
};

export const components = {
  Button,
  Input,
  Textarea,
  Heading,
  Link,
  Tabs,
  Modal,
  Drawer,
  Progress,
  Table,
  Tooltip,
  Spinner,
};
