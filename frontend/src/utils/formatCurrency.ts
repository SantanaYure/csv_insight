const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const compactCurrencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
});

/** Formata um valor em reais: 1250000 -> "R$ 1.250.000,00". */
export function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

/** Versão sem centavos, usada nos eixos dos gráficos. */
export function formatCurrencyCompact(value: number): string {
  return compactCurrencyFormatter.format(value);
}
