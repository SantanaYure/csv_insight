import type { Dataset, DatasetColumn, DatasetTable } from '../../types/dataset';
import type { DataRow } from '../ingestion/inferColumns';

export interface TableRole {
  table: DatasetTable;
  rows: DataRow[];
}

export interface NotasRole extends TableRole {
  dateColumn: string | null;
  totalColumn: string | null;
  supplierColumn: string | null;
  paymentColumn: string | null;
  taxColumn: string | null;
  idColumn: string | null;
}

export interface ItensRole extends TableRole {
  productColumn: string | null;
  quantityColumn: string | null;
  unitPriceColumn: string | null;
  totalColumn: string | null;
  unitColumn: string | null;
  notaColumn: string | null;
}

export interface FornecedoresRole extends TableRole {
  idColumn: string | null;
  nameColumn: string | null;
  cityColumn: string | null;
  stateColumn: string | null;
}

export interface DatasetSemantics {
  dataset: Dataset;
  rowsByTable: Record<string, DataRow[]>;
  notas: NotasRole | null;
  itens: ItensRole | null;
  fornecedores: FornecedoresRole | null;
}

function deburr(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

/** Procura a primeira coluna cujo nome contenha um dos termos informados. */
function findColumn(
  columns: DatasetColumn[],
  terms: string[],
  filter?: (column: DatasetColumn) => boolean,
): string | null {
  for (const term of terms) {
    const match = columns.find(
      (column) => deburr(column.name).includes(term) && (!filter || filter(column)),
    );
    if (match) return match.name;
  }
  return null;
}

function findByType(
  columns: DatasetColumn[],
  types: DatasetColumn['dataType'][],
): string | null {
  return columns.find((column) => types.includes(column.dataType))?.name ?? null;
}

const isNumeric = (column: DatasetColumn) =>
  column.dataType === 'number' || column.dataType === 'currency';

/**
 * Identifica o papel de cada tabela do conjunto (notas, itens e fornecedores)
 * a partir dos nomes e tipos das colunas. Tabelas que não se encaixam em
 * nenhum papel continuam disponíveis em `rowsByTable`.
 */
export function buildSemantics(
  dataset: Dataset,
  rowsByTable: Record<string, DataRow[]>,
): DatasetSemantics {
  const withRows = dataset.tables.map((table) => ({
    table,
    rows: rowsByTable[table.id] ?? [],
  }));

  const scoreNotas = ({ table }: TableRole) =>
    score(table, [
      [/nota|nfe|nfce|fiscal|venda|compra/, 3],
      [/data|emissao/, 2],
      // Cobre tanto "valor_total"/"total" quanto variações como
      // "valor nota fiscal", comuns em exportações de portais fiscais.
      [/valor_total|total|valor.*nota|valor.*fiscal/, 2],
    ]);

  const scoreItens = ({ table }: TableRole) =>
    score(table, [
      [/item|produto|linha/, 3],
      [/quantidade|qtd/, 2],
      [/valor_unitario|unitario/, 2],
    ]);

  const scoreFornecedores = ({ table }: TableRole) =>
    score(table, [
      [/fornecedor|emitente|cliente|empresa/, 3],
      [/razao_social|razao|nome/, 2],
      [/cnpj|cpf/, 2],
    ]);

  const assigned = assignRoles(withRows, {
    notas: scoreNotas,
    itens: scoreItens,
    fornecedores: scoreFornecedores,
  });
  const notasTable = assigned.notas;
  const itensTable = assigned.itens;
  const fornecedoresTable = assigned.fornecedores;

  return {
    dataset,
    rowsByTable,
    notas: notasTable
      ? {
          ...notasTable,
          idColumn: findColumn(notasTable.table.columns, ['id_nota', 'id']),
          dateColumn:
            findColumn(notasTable.table.columns, ['data_emissao', 'emissao', 'data']) ??
            findByType(notasTable.table.columns, ['date']),
          totalColumn:
            findColumn(notasTable.table.columns, ['valor_total', 'total'], isNumeric) ??
            findByType(notasTable.table.columns, ['currency']),
          supplierColumn: findColumn(notasTable.table.columns, ['id_fornecedor', 'fornecedor']),
          paymentColumn: findColumn(notasTable.table.columns, ['forma_pagamento', 'pagamento']),
          taxColumn: findColumn(notasTable.table.columns, ['tributo', 'imposto'], isNumeric),
        }
      : null,
    itens: itensTable
      ? {
          ...itensTable,
          // 'descricao' vem antes do genérico 'produto' porque colunas como
          // "Número Produto" (um código/sequencial, não o nome do item)
          // também contêm a palavra "produto" e viriam antes na ordem das
          // colunas em muitas exportações reais. O filtro de tipo texto é
          // uma segunda proteção contra pegar uma coluna numérica.
          productColumn: findColumn(
            itensTable.table.columns,
            ['descricao_produto', 'descricao', 'produto', 'item'],
            (column) => column.dataType === 'string',
          ),
          quantityColumn: findColumn(itensTable.table.columns, ['quantidade', 'qtd'], isNumeric),
          unitPriceColumn: findColumn(
            itensTable.table.columns,
            ['valor_unitario', 'unitario', 'preco'],
            isNumeric,
          ),
          totalColumn: findColumn(itensTable.table.columns, ['valor_total', 'total'], isNumeric),
          unitColumn: findColumn(itensTable.table.columns, ['unidade', 'un']),
          notaColumn: findColumn(itensTable.table.columns, ['id_nota', 'nota']),
        }
      : null,
    fornecedores: fornecedoresTable
      ? {
          ...fornecedoresTable,
          idColumn: findColumn(fornecedoresTable.table.columns, ['id_fornecedor', 'id']),
          nameColumn: findColumn(fornecedoresTable.table.columns, [
            'razao_social',
            'nome_fantasia',
            'razao',
            'nome',
          ]),
          cityColumn: findColumn(fornecedoresTable.table.columns, ['cidade', 'municipio']),
          stateColumn: findColumn(fornecedoresTable.table.columns, ['uf', 'estado']),
        }
      : null,
  };
}

function score(table: DatasetTable, rules: [RegExp, number][]): number {
  const haystack = deburr(
    [table.name, table.fileName, ...table.columns.map((column) => column.name)].join(' '),
  );
  return rules.reduce((total, [pattern, weight]) => (pattern.test(haystack) ? total + weight : total), 0);
}

type RoleName = 'notas' | 'itens' | 'fornecedores';

/**
 * Atribui cada papel à sua melhor tabela, considerando os três papéis ao
 * mesmo tempo (em vez de escolher "notas" isoladamente e só depois deixar
 * "itens" competir pelo que sobrou). Isso importa porque, em exportações
 * reais, a tabela de itens costuma repetir todas as colunas do cabeçalho da
 * nota — então ela pode pontuar igual para "notas" e para "itens".
 *
 * Nesses empates, a pista mais confiável é o tamanho relativo das tabelas:
 * o cabeçalho (notas) normalmente tem menos linhas que o detalhe (itens),
 * numa relação um-para-muitos. Essa preferência entra como um pequeno ajuste
 * na pontuação — pequeno o bastante para nunca decidir sozinho (a diferença
 * de palavras-chave continua valendo mais), mas suficiente para desempatar.
 */
function assignRoles(
  candidates: TableRole[],
  scorers: Record<RoleName, (candidate: TableRole) => number>,
): Record<RoleName, TableRole | null> {
  const roles = Object.keys(scorers) as RoleName[];
  const rowCounts = candidates.map((candidate) => candidate.rows.length);
  const minRows = Math.min(...rowCounts);
  const maxRows = Math.max(...rowCounts);
  const spread = maxRows - minRows;

  /** 0 para a menor tabela do conjunto, 1 para a maior. */
  const sizeRank = (candidate: TableRole) =>
    spread > 0 ? (candidate.rows.length - minRows) / spread : 0.5;

  const pairs = roles
    .flatMap((role) =>
      candidates.map((candidate) => {
        const base = scorers[role](candidate);
        const rank = sizeRank(candidate);
        const tiebreak = role === 'notas' ? (1 - rank) * 0.9 : role === 'itens' ? rank * 0.9 : 0;
        return { role, candidate, score: base + tiebreak, qualifies: base >= 3 };
      }),
    )
    // Exige ao menos duas evidências reais (sem contar o desempate) para
    // evitar associações arbitrárias.
    .filter((pair) => pair.qualifies)
    .sort((a, b) => b.score - a.score);

  const result: Record<RoleName, TableRole | null> = { notas: null, itens: null, fornecedores: null };
  const takenTables = new Set<string>();
  const takenRoles = new Set<RoleName>();

  for (const pair of pairs) {
    if (takenRoles.has(pair.role) || takenTables.has(pair.candidate.table.id)) continue;
    result[pair.role] = pair.candidate;
    takenRoles.add(pair.role);
    takenTables.add(pair.candidate.table.id);
  }

  return result;
}
