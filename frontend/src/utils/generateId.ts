let counter = 0;

/** Identificador estável para mensagens e itens de histórico. */
export function generateId(prefix = 'id'): string {
  counter += 1;
  const random = Math.random().toString(36).slice(2, 8);
  return `${prefix}-${Date.now().toString(36)}-${counter}-${random}`;
}
