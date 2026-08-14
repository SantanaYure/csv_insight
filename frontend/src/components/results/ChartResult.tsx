import { Box, Text, useToken } from '@chakra-ui/react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { ChartSpec, ChartType } from '../../types/query';
import { formatCurrency, formatCurrencyCompact } from '../../utils/formatCurrency';
import { formatNumber } from '../../utils/formatNumber';

export interface ChartResultProps {
  /** API visual: aceita `type`, `title`, `xKey`, `yKey` e `data`. */
  type: ChartType;
  title: string;
  xKey: string;
  yKey: string;
  data: Record<string, string | number>[];
  caption?: string;
  yLabel?: string;
  valueFormat?: 'number' | 'currency';
  /** Valor do eixo X que recebe o tom mais forte de amarelo. */
  highlightKey?: string;
  height?: number;
  /** Oculta o título quando o card já exibe um cabeçalho próprio. */
  hideTitle?: boolean;
}

/**
 * Renderiza gráficos de barras, linhas, área e pizza com Recharts,
 * respeitando o tema e usando o amarelo como cor principal.
 */
export function ChartResult({
  type,
  title,
  xKey,
  yKey,
  data,
  caption,
  yLabel,
  valueFormat = 'number',
  highlightKey,
  height = 240,
  hideTitle = false,
}: ChartResultProps) {
  const [primary, strong, soft, grid, axis, surface, border, textPrimary] = useToken('colors', [
    'brand.primary',
    'brand.primaryHover',
    'brand.soft',
    'chart.grid',
    'chart.axis',
    'background.surface',
    'border.default',
    'text.primary',
  ]);

  const formatValue = (value: number) =>
    valueFormat === 'currency' ? formatCurrency(value) : formatNumber(value);

  const formatAxisValue = (value: number) =>
    valueFormat === 'currency' ? formatCurrencyCompact(value) : formatNumber(value);

  const axisProps = {
    stroke: axis,
    tick: { fill: axis, fontSize: 12 },
    tickLine: false,
  };

  const tooltipProps = {
    cursor: { fill: soft, opacity: 0.45 },
    contentStyle: {
      background: surface,
      border: `1px solid ${border}`,
      borderRadius: '10px',
      boxShadow: 'none',
      color: textPrimary,
      fontSize: '13px',
    },
    labelStyle: { color: textPrimary, fontWeight: 600, marginBottom: 4 },
    formatter: (value: number | string) => [
      formatValue(Number(value)),
      yLabel ?? title,
    ] as [string, string],
  };

  return (
    <Box>
      {!hideTitle ? (
        <Text m={0} fontSize="16px" fontWeight={600} color="text.primary">
          {title}
        </Text>
      ) : null}
      {caption ? (
        <Text mt="6px" fontSize="13.5px" color="text.muted">
          {caption}
        </Text>
      ) : null}

      <Box mt={hideTitle && !caption ? 0 : '20px'} height={`${height}px`} width="100%">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </Box>
    </Box>
  );

  function renderChart() {
    const margin = { top: 8, right: 8, bottom: 0, left: 4 };

    if (type === 'line') {
      return (
        <LineChart data={data} margin={margin}>
          <CartesianGrid stroke={grid} vertical={false} />
          <XAxis dataKey={xKey} {...axisProps} axisLine={{ stroke: border }} />
          <YAxis {...axisProps} axisLine={false} width={78} tickFormatter={formatAxisValue} />
          <Tooltip {...tooltipProps} />
          <Line
            type="monotone"
            dataKey={yKey}
            stroke={strong}
            strokeWidth={2.5}
            dot={{ r: 3.5, fill: primary, stroke: strong, strokeWidth: 1.5 }}
            activeDot={{ r: 5.5 }}
            name={yLabel ?? title}
          />
        </LineChart>
      );
    }

    if (type === 'area') {
      return (
        <AreaChart data={data} margin={margin}>
          <defs>
            <linearGradient id="csv-insight-area" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={primary} stopOpacity={0.7} />
              <stop offset="100%" stopColor={primary} stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={grid} vertical={false} />
          <XAxis dataKey={xKey} {...axisProps} axisLine={{ stroke: border }} />
          <YAxis {...axisProps} axisLine={false} width={78} tickFormatter={formatAxisValue} />
          <Tooltip {...tooltipProps} />
          <Area
            type="monotone"
            dataKey={yKey}
            stroke={strong}
            strokeWidth={2.5}
            fill="url(#csv-insight-area)"
            name={yLabel ?? title}
          />
        </AreaChart>
      );
    }

    if (type === 'pie') {
      return (
        <PieChart margin={margin}>
          <Tooltip {...tooltipProps} cursor={false} />
          <Legend
            verticalAlign="bottom"
            iconType="circle"
            iconSize={9}
            wrapperStyle={{ fontSize: 12.5, color: axis }}
          />
          <Pie
            data={data}
            dataKey={yKey}
            nameKey={xKey}
            innerRadius="46%"
            outerRadius="76%"
            paddingAngle={2}
            stroke={surface}
            strokeWidth={2}
          >
            {data.map((entry, index) => (
              <Cell
                key={String(entry[xKey])}
                fill={[strong, primary, soft, grid][index % 4]}
              />
            ))}
          </Pie>
        </PieChart>
      );
    }

    return (
      <BarChart data={data} margin={margin}>
        <CartesianGrid stroke={grid} vertical={false} />
        <XAxis dataKey={xKey} {...axisProps} axisLine={{ stroke: border }} />
        <YAxis {...axisProps} axisLine={false} width={78} tickFormatter={formatAxisValue} />
        <Tooltip {...tooltipProps} />
        <Bar dataKey={yKey} radius={[5, 5, 0, 0]} name={yLabel ?? title} maxBarSize={64}>
          {data.map((entry) => (
            <Cell
              key={String(entry[xKey])}
              fill={highlightKey && entry[xKey] === highlightKey ? strong : primary}
            />
          ))}
        </Bar>
      </BarChart>
    );
  }
}

/** Adaptador que recebe a especificação completa do gráfico. */
export function ChartResultFromSpec({
  chart,
  height,
  hideTitle,
}: {
  chart: ChartSpec;
  height?: number;
  hideTitle?: boolean;
}) {
  return (
    <ChartResult
      type={chart.type}
      title={chart.title}
      xKey={chart.xKey}
      yKey={chart.yKey}
      data={chart.data}
      caption={chart.caption}
      yLabel={chart.yLabel}
      valueFormat={chart.valueFormat}
      highlightKey={chart.highlightKey}
      height={height}
      hideTitle={hideTitle}
    />
  );
}
