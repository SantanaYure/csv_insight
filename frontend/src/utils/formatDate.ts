const dateFormatter = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
});

const timeFormatter = new Intl.DateTimeFormat('pt-BR', {
  hour: '2-digit',
  minute: '2-digit',
});

/** "01/08/2026". */
export function formatDate(value: string | Date): string {
  return dateFormatter.format(toDate(value));
}

/** "09:14". */
export function formatTime(value: string | Date): string {
  return timeFormatter.format(toDate(value));
}

/** "01/08/2026 · 09:14". */
export function formatDateTime(value: string | Date): string {
  const date = toDate(value);
  return `${dateFormatter.format(date)} · ${timeFormatter.format(date)}`;
}

/**
 * Data relativa usada no histórico: "Hoje · 14:32", "Ontem · 17:20"
 * ou "24/07/2026 · 10:05" para datas mais antigas.
 */
export function formatRelativeDateTime(value: string | Date): string {
  const date = toDate(value);
  const time = timeFormatter.format(date);
  const days = differenceInCalendarDays(new Date(), date);

  if (days === 0) return `Hoje · ${time}`;
  if (days === 1) return `Ontem · ${time}`;
  return `${dateFormatter.format(date)} · ${time}`;
}

function toDate(value: string | Date): Date {
  return value instanceof Date ? value : new Date(value);
}

function differenceInCalendarDays(from: Date, to: Date): number {
  const startFrom = new Date(from.getFullYear(), from.getMonth(), from.getDate());
  const startTo = new Date(to.getFullYear(), to.getMonth(), to.getDate());
  return Math.round((startFrom.getTime() - startTo.getTime()) / 86_400_000);
}
