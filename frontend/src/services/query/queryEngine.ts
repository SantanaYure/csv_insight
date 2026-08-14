import type { QueryResult } from '../../types/query';
import { formatCurrency } from '../../utils/formatCurrency';
import { formatDate } from '../../utils/formatDate';
import { formatNumber } from '../../utils/formatNumber';
import type { CellValue, DataRow } from '../ingestion/inferColumns';
import type { DatasetSemantics } from './semantics';

const TOP_N = 5;

const MONTHS = [
  'jan',
  'fev',
  'mar',
  'abr',
  'mai',
  'jun',
  'jul',
  'ago',
  'set',
  'out',
  'nov',
  'dez',
];

interface Handler {
  /** Todos os termos precisam aparecer na pergunta normalizada. */
  match: string[];
  /** Nenhum destes termos pode aparecer. */
  exclude?: string[];
  run: (semantics: DatasetSemantics) => QueryResult | null;
}

export function normalizeQuestion(question: string): string {
  return question
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Responde perguntas em linguagem natural calculando os valores diretamente
 * sobre as linhas carregadas do ZIP. Não há nenhum resultado pré-definido.
 */
export function answerQuestion(
  semantics: DatasetSemantics,
  question: string,
): QueryResult {
  const normalized = normalizeQuestion(question);
  if (!normalized) return notUnderstood(semantics);

  for (const handler of handlers) {
    const matches =
      handler.match.every((term) => normalized.includes(term)) &&
      !(handler.exclude ?? []).some((term) => normalized.includes(term));

    if (!matches) continue;

    const result = handler.run(semantics);
    if (result) return result;
  }

  return notUnderstood(semantics);
}

const handlers: Handler[] = [
  // Total por mês
  {
    match: ['mes'],
    run: (s) => {
      const notas = s.notas;
      if (!notas?.dateColumn || !notas.totalColumn) return null;

      const buckets = new Map<string, { label: string; total: number }>();
      notas.rows.forEach((row) => {
        const date = toDate(row[notas.dateColumn as string]);
        const value = toNumber(row[notas.totalColumn as string]);
        if (!date || value === null) return;

        const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        const label = `${MONTHS[date.getMonth()]}/${date.getFullYear()}`;
        const bucket = buckets.get(key) ?? { label, total: 0 };
        bucket.total += value;
        buckets.set(key, bucket);
      });

      if (buckets.size === 0) return null;

      const data = [...buckets.entries()]
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([, bucket]) => ({ mes: bucket.label, valor: round(bucket.total) }));

      const peak = [...data].sort((a, b) => b.valor - a.valor)[0];

      return {
        type: 'chart',
        answer: `O maior volume foi em ${peak.mes}, com ${formatCurrency(peak.valor)}.`,
        chart: {
          type: data.length > 6 ? 'line' : 'bar',
          title: 'Total gasto por mês',
          caption: `Valores em reais · ${data.length} ${data.length === 1 ? 'mês' : 'meses'} com registros`,
          xKey: 'mes',
          yKey: 'valor',
          yLabel: 'Total gasto',
          valueFormat: 'currency',
          highlightKey: peak.mes,
          data,
        },
      };
    },
  },

  // Maiores fornecedores
  {
    match: ['fornecedor'],
    run: (s) => {
      const notas = s.notas;
      if (!notas?.totalColumn || !notas.supplierColumn) return null;

      const nameOf = supplierNameResolver(s);
      const buckets = new Map<string, { total: number; count: number }>();

      notas.rows.forEach((row) => {
        const key = nameOf(row[notas.supplierColumn as string]);
        const value = toNumber(row[notas.totalColumn as string]) ?? 0;
        const bucket = buckets.get(key) ?? { total: 0, count: 0 };
        bucket.total += value;
        bucket.count += 1;
        buckets.set(key, bucket);
      });

      if (buckets.size === 0) return null;

      const ranked = [...buckets.entries()]
        .sort((a, b) => b[1].total - a[1].total)
        .slice(0, TOP_N);

      const [topName, topBucket] = ranked[0];

      return {
        type: 'table',
        title: buckets.size <= TOP_N ? 'Fornecedores' : `Maiores fornecedores (top ${TOP_N})`,
        answer: `${topName} lidera com ${formatCurrency(topBucket.total)} em ${topBucket.count} ${topBucket.count === 1 ? 'nota' : 'notas'}.`,
        columns: [
          { key: 'fornecedor', label: 'Fornecedor', dataType: 'string' },
          { key: 'notas', label: 'Notas', dataType: 'number', align: 'right' },
          { key: 'valor', label: 'Valor total', dataType: 'currency', align: 'right' },
        ],
        rows: ranked.map(([name, bucket]) => ({
          fornecedor: name,
          notas: bucket.count,
          valor: round(bucket.total),
        })),
      };
    },
  },

  // Produto com maior quantidade
  {
    match: ['produto'],
    exclude: ['valor', 'caro', 'gasto'],
    run: (s) => {
      const itens = s.itens;
      if (!itens?.productColumn || !itens.quantityColumn) return null;

      const ranked = rankBy(
        itens.rows,
        itens.productColumn,
        itens.quantityColumn,
      ).slice(0, TOP_N);

      if (ranked.length === 0) return null;

      const [top] = ranked;

      return {
        type: 'combined',
        answer: `O produto ${top.key} apresentou o maior volume comprado, com ${formatNumber(top.value)} ${top.value === 1 ? 'unidade' : 'unidades'}.`,
        table: {
          columns: [
            { key: 'produto', label: 'Produto', dataType: 'string' },
            { key: 'quantidade', label: 'Qtd.', dataType: 'number', align: 'right' },
          ],
          rows: ranked.map((entry) => ({ produto: entry.key, quantidade: entry.value })),
        },
        chart: {
          chart: {
            type: 'bar',
            title: 'Quantidade comprada por produto',
            xKey: 'produto',
            yKey: 'quantidade',
            yLabel: 'Quantidade',
            valueFormat: 'number',
            highlightKey: top.key,
            data: ranked.map((entry) => ({ produto: entry.key, quantidade: entry.value })),
          },
        },
      };
    },
  },

  // Produtos por valor gasto
  {
    match: ['produto'],
    run: (s) => {
      const itens = s.itens;
      const valueColumn = itens?.totalColumn ?? itens?.unitPriceColumn;
      if (!itens?.productColumn || !valueColumn) return null;

      const ranked = rankBy(itens.rows, itens.productColumn, valueColumn).slice(0, TOP_N);
      if (ranked.length === 0) return null;

      return {
        type: 'table',
        title: `Produtos com maior valor (top ${TOP_N})`,
        answer: `${ranked[0].key} concentra ${formatCurrency(ranked[0].value)}.`,
        columns: [
          { key: 'produto', label: 'Produto', dataType: 'string' },
          { key: 'valor', label: 'Valor gasto', dataType: 'currency', align: 'right' },
        ],
        rows: ranked.map((entry) => ({ produto: entry.key, valor: round(entry.value) })),
      };
    },
  },

  // Forma de pagamento
  {
    match: ['pagamento'],
    run: (s) => {
      const notas = s.notas;
      if (!notas?.paymentColumn || !notas.totalColumn) return null;

      const ranked = rankBy(notas.rows, notas.paymentColumn, notas.totalColumn);
      if (ranked.length === 0) return null;

      return {
        type: 'chart',
        answer: `${ranked[0].key} responde por ${formatCurrency(ranked[0].value)}.`,
        chart: {
          type: 'pie',
          title: 'Valor por forma de pagamento',
          xKey: 'forma',
          yKey: 'valor',
          yLabel: 'Valor',
          valueFormat: 'currency',
          data: ranked.map((entry) => ({ forma: entry.key, valor: round(entry.value) })),
        },
      };
    },
  },

  // Tributos
  {
    match: ['tributo'],
    run: (s) => taxAnswer(s),
  },
  {
    match: ['imposto'],
    run: (s) => taxAnswer(s),
  },

  // Ticket médio
  {
    match: ['ticket medio'],
    run: (s) => ticketAnswer(s),
  },
  {
    match: ['media', 'nota'],
    run: (s) => ticketAnswer(s),
  },

  // Contagem de notas
  {
    match: ['quantas notas'],
    run: (s) => countNotas(s),
  },
  {
    match: ['numero de notas'],
    run: (s) => countNotas(s),
  },

  // Contagem de itens
  {
    match: ['quantos itens'],
    run: (s) => {
      const itens = s.itens;
      if (!itens) return null;

      const distinct = itens.productColumn
        ? new Set(itens.rows.map((row) => String(row[itens.productColumn as string] ?? ''))).size
        : null;

      return {
        type: 'text',
        answer: `Foram registrados ${formatNumber(itens.rows.length)} itens.`,
        detail: distinct
          ? `São ${formatNumber(distinct)} descrições de produto distintas.`
          : undefined,
      };
    },
  },

  // Item mais caro
  {
    match: ['mais caro'],
    run: (s) => {
      const itens = s.itens;
      if (!itens?.productColumn || !itens.unitPriceColumn) return null;

      const ranked = [...itens.rows]
        .map((row) => ({
          key: label(row[itens.productColumn as string]),
          value: toNumber(row[itens.unitPriceColumn as string]) ?? 0,
        }))
        .sort((a, b) => b.value - a.value)
        .slice(0, TOP_N);

      if (ranked.length === 0) return null;

      return {
        type: 'table',
        title: `Itens de maior valor unitário (top ${TOP_N})`,
        answer: `${ranked[0].key} tem o maior valor unitário: ${formatCurrency(ranked[0].value)}.`,
        columns: [
          { key: 'produto', label: 'Produto', dataType: 'string' },
          { key: 'valor', label: 'Valor unitário', dataType: 'currency', align: 'right' },
        ],
        rows: ranked.map((entry) => ({ produto: entry.key, valor: round(entry.value) })),
      };
    },
  },

  // Unidade de medida
  {
    match: ['unidade'],
    run: (s) => {
      const itens = s.itens;
      if (!itens?.unitColumn || !itens.quantityColumn) return null;

      const ranked = rankBy(itens.rows, itens.unitColumn, itens.quantityColumn);
      if (ranked.length === 0) return null;

      return {
        type: 'table',
        title: 'Quantidade por unidade de medida',
        columns: [
          { key: 'unidade', label: 'Unidade', dataType: 'string' },
          { key: 'quantidade', label: 'Quantidade', dataType: 'number', align: 'right' },
        ],
        rows: ranked.map((entry) => ({ unidade: entry.key, quantidade: round(entry.value) })),
      };
    },
  },

  // Total geral — fica por último para não capturar as perguntas específicas.
  {
    match: ['total'],
    run: (s) => totalAnswer(s),
  },
  {
    match: ['gastei'],
    run: (s) => totalAnswer(s),
  },
  {
    match: ['quanto', 'gast'],
    run: (s) => totalAnswer(s),
  },
];

function totalAnswer(s: DatasetSemantics): QueryResult | null {
  const notas = s.notas;
  if (!notas?.totalColumn) return null;

  const values = notas.rows
    .map((row) => toNumber(row[notas.totalColumn as string]))
    .filter((value): value is number => value !== null);

  if (values.length === 0) return null;

  const total = values.reduce((sum, value) => sum + value, 0);

  return {
    type: 'text',
    answer: `O valor total das compras foi de ${formatCurrency(round(total))}.`,
    detail: buildPeriodDetail(s, values.length),
  };
}

function ticketAnswer(s: DatasetSemantics): QueryResult | null {
  const notas = s.notas;
  if (!notas?.totalColumn) return null;

  const values = notas.rows
    .map((row) => toNumber(row[notas.totalColumn as string]))
    .filter((value): value is number => value !== null);

  if (values.length === 0) return null;

  const total = values.reduce((sum, value) => sum + value, 0);
  const average = total / values.length;
  // Math.max(...values)/Math.min(...values) estourariam a pilha de chamadas
  // com dezenas de milhares de notas (o limite de argumentos de uma função
  // é bem menor que isso); reduce percorre o array sem essa limitação.
  const max = values.reduce((current, value) => Math.max(current, value), -Infinity);
  const min = values.reduce((current, value) => Math.min(current, value), Infinity);

  return {
    type: 'text',
    answer: `O ticket médio por nota foi de ${formatCurrency(round(average))}.`,
    detail: `Considerando ${formatNumber(values.length)} notas, entre ${formatCurrency(round(min))} e ${formatCurrency(round(max))}.`,
  };
}

function taxAnswer(s: DatasetSemantics): QueryResult | null {
  const notas = s.notas;
  if (!notas?.taxColumn) return null;

  const taxes = notas.rows
    .map((row) => toNumber(row[notas.taxColumn as string]))
    .filter((value): value is number => value !== null);

  if (taxes.length === 0) return null;

  const totalTax = taxes.reduce((sum, value) => sum + value, 0);
  const totalValue = notas.totalColumn
    ? notas.rows
        .map((row) => toNumber(row[notas.totalColumn as string]) ?? 0)
        .reduce((sum, value) => sum + value, 0)
    : 0;

  const share = totalValue > 0 ? (totalTax / totalValue) * 100 : null;

  return {
    type: 'text',
    answer: `Os tributos aproximados somam ${formatCurrency(round(totalTax))}.`,
    detail:
      share !== null
        ? `Isso representa ${share.toFixed(1).replace('.', ',')}% do valor total das notas.`
        : undefined,
  };
}

function countNotas(s: DatasetSemantics): QueryResult | null {
  const notas = s.notas;
  if (!notas) return null;

  return {
    type: 'text',
    answer: `Foram encontradas ${formatNumber(notas.rows.length)} notas fiscais.`,
    detail: buildPeriodDetail(s, notas.rows.length),
  };
}

function buildPeriodDetail(s: DatasetSemantics, count: number): string | undefined {
  const notas = s.notas;
  if (!notas?.dateColumn) return `Considerando ${formatNumber(count)} notas fiscais.`;

  const dates = notas.rows
    .map((row) => toDate(row[notas.dateColumn as string]))
    .filter((date): date is Date => date !== null)
    .sort((a, b) => a.getTime() - b.getTime());

  if (dates.length === 0) return `Considerando ${formatNumber(count)} notas fiscais.`;

  const first = formatDate(dates[0]);
  const last = formatDate(dates[dates.length - 1]);

  return first === last
    ? `Considerando ${formatNumber(count)} notas fiscais emitidas em ${first}.`
    : `Considerando ${formatNumber(count)} notas fiscais emitidas entre ${first} e ${last}.`;
}

function notUnderstood(s: DatasetSemantics): QueryResult {
  const topics: string[] = [];
  if (s.notas?.totalColumn) topics.push('valores e períodos');
  if (s.fornecedores || s.notas?.supplierColumn) topics.push('fornecedores');
  if (s.itens?.productColumn) topics.push('produtos e quantidades');

  const tables = s.dataset.tables.map((table) => table.name).join(', ');

  return {
    type: 'error',
    title: 'Não foi possível responder',
    message: 'Não encontrei uma forma de calcular essa resposta com os dados carregados.',
    suggestion: topics.length
      ? `Tente perguntar sobre ${topics.join(', ')}. Tabelas disponíveis: ${tables}.`
      : `Tabelas disponíveis: ${tables}.`,
  };
}

/** Agrupa por uma coluna e soma outra, do maior para o menor. */
function rankBy(
  rows: DataRow[],
  keyColumn: string,
  valueColumn: string,
): { key: string; value: number }[] {
  const buckets = new Map<string, number>();

  rows.forEach((row) => {
    const key = label(row[keyColumn]);
    const value = toNumber(row[valueColumn]);
    if (value === null) return;
    buckets.set(key, (buckets.get(key) ?? 0) + value);
  });

  return [...buckets.entries()]
    .map(([key, value]) => ({ key, value: round(value) }))
    .sort((a, b) => b.value - a.value);
}

/** Resolve o id do fornecedor para a razão social, quando disponível. */
function supplierNameResolver(s: DatasetSemantics): (value: CellValue) => string {
  const fornecedores = s.fornecedores;
  if (!fornecedores?.idColumn || !fornecedores.nameColumn) return (value) => label(value);

  const byId = new Map<string, string>();
  fornecedores.rows.forEach((row) => {
    const id = label(row[fornecedores.idColumn as string]);
    const name = label(row[fornecedores.nameColumn as string]);
    if (id) byId.set(id, name);
  });

  return (value) => {
    const key = label(value);
    return byId.get(key) ?? key;
  };
}

function label(value: CellValue): string {
  if (value === null || value === undefined || value === '') return 'Não informado';
  return String(value);
}

function toNumber(value: CellValue): number | null {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  if (typeof value !== 'string') return null;
  const parsed = Number(value.replace(',', '.'));
  return Number.isFinite(parsed) ? parsed : null;
}

function toDate(value: CellValue): Date | null {
  if (value === null || value === undefined) return null;
  const raw = String(value).trim();
  if (!raw) return null;

  // dd/mm/aaaa
  const br = /^(\d{2})\/(\d{2})\/(\d{4})/.exec(raw);
  if (br) return new Date(Number(br[3]), Number(br[2]) - 1, Number(br[1]));

  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

/** Perguntas sugeridas geradas conforme o que existe no conjunto carregado. */
export function buildSuggestedQuestions(s: DatasetSemantics): string[] {
  const suggestions: string[] = [];

  if (s.notas?.totalColumn) suggestions.push('Qual foi o valor total das compras?');
  if (s.notas?.supplierColumn) suggestions.push('Quais foram os maiores fornecedores?');
  if (s.notas?.dateColumn && s.notas.totalColumn) {
    suggestions.push('Qual foi o total gasto em cada mês?');
  }
  if (s.itens?.productColumn && s.itens.quantityColumn) {
    suggestions.push('Qual produto teve a maior quantidade comprada?');
  }
  if (s.itens?.productColumn && (s.itens.totalColumn || s.itens.unitPriceColumn)) {
    suggestions.push('Quais produtos tiveram o maior valor gasto?');
  }
  if (s.notas?.paymentColumn) suggestions.push('Como foi distribuído o valor por forma de pagamento?');
  if (s.notas?.taxColumn) suggestions.push('Quanto foi pago em tributos aproximados?');
  if (s.notas?.totalColumn) suggestions.push('Qual foi o ticket médio por nota?');

  if (suggestions.length === 0) {
    suggestions.push('Quantos registros existem no conjunto de dados?');
  }

  return suggestions.slice(0, 6);
}
