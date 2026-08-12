import { Box, Flex, Grid, Text } from '@chakra-ui/react';
import { BarChart3, Table2 } from 'lucide-react';

const MONTHS = [
  { label: 'jan', height: '63%', strong: false },
  { label: 'fev', height: '69%', strong: false },
  { label: 'mar', height: '58%', strong: false },
  { label: 'abr', height: '82%', strong: true },
  { label: 'mai', height: '100%', strong: true },
  { label: 'jun', height: '93%', strong: true },
];

const ROWS = [
  { month: 'Maio', value: 'R$ 134.000,00' },
  { month: 'Junho', value: 'R$ 125.000,00' },
  { month: 'Abril', value: 'R$ 110.000,00' },
];

/** Mockup estático da tela de consulta exibido ao lado do hero. */
export function AppPreview() {
  return (
    <Box
      aria-hidden="true"
      bg="background.surface"
      borderWidth="1px"
      borderStyle="solid"
      borderColor="border.default"
      borderRadius="3xl"
      boxShadow="floating"
      overflow="hidden"
    >
      <Flex
        align="center"
        gap="10px"
        px="18px"
        py="14px"
        borderBottomWidth="1px"
        borderBottomStyle="solid"
        borderColor="border.default"
        bg="background.subtle"
      >
        <Box as="span" color="text.muted">
          <Table2 size={15} strokeWidth={1.8} />
        </Box>
        <Text m={0} fontSize="13px" fontWeight={600} color="text.secondary">
          Consulta · notas_fiscais_2025
        </Text>
        <Box flex="1" />
        <Flex align="center" gap="6px" fontSize="11.5px" fontWeight={600} color="text.muted">
          <Box as="span" width="6px" height="6px" borderRadius="full" bg="brand.primaryHover" />
          pronto
        </Flex>
      </Flex>

      <Flex direction="column" gap="14px" p="18px">
        <Flex justify="flex-end">
          <Text
            m={0}
            maxW="78%"
            px="15px"
            py="11px"
            borderRadius="14px 14px 4px 14px"
            bg="chat.userBg"
            color="chat.userText"
            fontSize="14px"
            lineHeight={1.5}
          >
            Qual foi o total gasto em cada mês?
          </Text>
        </Flex>

        <Flex gap="10px">
          <Box
            as="span"
            flex="none"
            display="grid"
            placeItems="center"
            width="28px"
            height="28px"
            borderRadius="md"
            bg="brand.primary"
            color="#111111"
          >
            <BarChart3 size={15} strokeWidth={2} />
          </Box>

          <Box
            flex="1"
            minW={0}
            p="14px"
            bg="background.surface"
            borderWidth="1px"
            borderStyle="solid"
            borderColor="border.default"
            borderRadius="14px"
            boxShadow="card"
          >
            <Text m={0} mb="12px" fontSize="14px" lineHeight={1.55} color="text.primary">
              Maio concentrou o maior volume, com{' '}
              <Text as="strong" fontWeight={600}>
                R$ 134.000,00
              </Text>
              .
            </Text>

            <Flex
              align="flex-end"
              gap="7px"
              height="86px"
              px="4px"
              pt="8px"
              borderBottomWidth="1px"
              borderBottomStyle="solid"
              borderColor="border.default"
              sx={{
                backgroundImage:
                  'repeating-linear-gradient(to top, var(--chakra-colors-chart-grid) 0 1px, transparent 1px 33.33%)',
              }}
            >
              {MONTHS.map((month) => (
                <Box
                  key={month.label}
                  flex="1"
                  height={month.height}
                  borderRadius="4px 4px 0 0"
                  bg={month.strong ? 'brand.primary' : 'brand.soft'}
                />
              ))}
            </Flex>

            <Flex gap="7px" mt="7px">
              {MONTHS.map((month) => (
                <Text key={month.label} flex="1" textAlign="center" fontSize="10.5px" color="text.muted">
                  {month.label}
                </Text>
              ))}
            </Flex>

            <Box
              mt="14px"
              borderWidth="1px"
              borderStyle="solid"
              borderColor="border.default"
              borderRadius="lg"
              overflow="hidden"
            >
              <Grid
                templateColumns="1fr auto"
                gap="12px"
                px="12px"
                py="8px"
                bg="background.subtle"
                fontSize="11px"
                fontWeight={600}
                letterSpacing="0.04em"
                textTransform="uppercase"
                color="text.muted"
              >
                <Box as="span">Mês</Box>
                <Box as="span">Valor</Box>
              </Grid>
              {ROWS.map((row) => (
                <Grid
                  key={row.month}
                  templateColumns="1fr auto"
                  gap="12px"
                  px="12px"
                  py="9px"
                  borderTopWidth="1px"
                  borderTopStyle="solid"
                  borderColor="border.default"
                  fontSize="13px"
                  color="text.primary"
                >
                  <Box as="span">{row.month}</Box>
                  <Box as="span" fontWeight={600}>
                    {row.value}
                  </Box>
                </Grid>
              ))}
            </Box>
          </Box>
        </Flex>
      </Flex>
    </Box>
  );
}
