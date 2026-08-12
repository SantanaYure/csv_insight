import { Fragment, type ReactNode } from 'react';

const SPLIT_PATTERN = /(R\$\s?[\d.]+(?:,\d{2})?|\d[\d.]*(?:,\d+)?%?)/g;
/** Cópia sem a flag `g` para testar cada trecho sem estado compartilhado. */
const TEST_PATTERN = /^(R\$\s?[\d.]+(?:,\d{2})?|\d[\d.]*(?:,\d+)?%?)$/;

/**
 * Destaca valores monetários e numéricos dentro de uma frase, reproduzindo o
 * `<strong>` usado nas respostas do design.
 */
export function highlightNumbers(text: string): ReactNode {
  const parts = text.split(SPLIT_PATTERN);

  return parts.map((part, index) =>
    TEST_PATTERN.test(part) ? (
      <strong key={`${part}-${index}`} style={{ fontWeight: 600 }}>
        {part}
      </strong>
    ) : (
      <Fragment key={`${part}-${index}`}>{part}</Fragment>
    ),
  );
}
