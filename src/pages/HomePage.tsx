import { Box, Button, Flex, Grid, Heading, Link as ChakraLink, Text } from '@chakra-ui/react';
import {
  AlignLeft,
  BarChart3,
  Clock,
  MessageSquare,
  Table2,
  Upload,
  type LucideIcon,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { PageContainer } from '../components/common/PageContainer';
import { SurfaceCard } from '../components/common/SurfaceCard';
import { AppPreview } from '../components/home/AppPreview';
import { pageGutter } from '../theme';

const STEPS = [
  { number: '01', title: 'Envie o ZIP', description: 'Um arquivo com os CSVs e o dicionário de dados.' },
  { number: '02', title: 'Revise os dados', description: 'Confira tabelas, colunas e tipos identificados.' },
  { number: '03', title: 'Faça perguntas', description: 'Escreva como falaria com um analista.' },
  {
    number: '04',
    title: 'Visualize os resultados',
    description: 'Texto, tabela ou gráfico, conforme a pergunta.',
  },
];

const FEATURES: { icon: LucideIcon; title: string; description: string }[] = [
  {
    icon: Upload,
    title: 'Upload de múltiplos CSVs',
    description: 'Um ZIP com todas as tabelas relacionadas do seu domínio.',
  },
  {
    icon: MessageSquare,
    title: 'Consulta em linguagem natural',
    description: 'Perguntas escritas em português, sem SQL.',
  },
  {
    icon: AlignLeft,
    title: 'Respostas em texto',
    description: 'Explicações curtas e diretas, com os números citados.',
  },
  {
    icon: Table2,
    title: 'Tabelas',
    description: 'Resultados tabulares com ordenação e download.',
  },
  {
    icon: BarChart3,
    title: 'Gráficos',
    description: 'Séries e comparações renderizadas automaticamente.',
  },
  {
    icon: Clock,
    title: 'Histórico',
    description: 'Toda consulta fica registrada para revisitar depois.',
  },
];

export function HomePage() {
  const navigate = useNavigate();

  return (
    <Box>
      {/* Hero */}
      <PageContainer as="section" pt={{ base: '48px', lg: '64px' }} pb={{ base: '56px', lg: '72px' }}>
        <Grid
          templateColumns={{ base: '1fr', lg: '1.05fr .95fr' }}
          gap={{ base: '40px', lg: '56px' }}
          alignItems="center"
        >
          <Box>
            <Flex
              as="span"
              display="inline-flex"
              align="center"
              gap="8px"
              height="30px"
              px="12px"
              borderRadius="full"
              bg="brand.tint"
              borderWidth="1px"
              borderStyle="solid"
              borderColor="brand.soft"
              fontSize="12.5px"
              fontWeight={600}
              color="text.secondary"
            >
              <Box as="span" width="6px" height="6px" borderRadius="full" bg="brand.primaryHover" />
              Análise por linguagem natural
            </Flex>

            <Heading as="h1" size="display" mt="20px" color="text.primary">
              Consulte seus dados usando linguagem natural
            </Heading>

            <Text mt="20px" maxW="520px" fontSize="18px" lineHeight={1.6} color="text.muted">
              Envie arquivos CSV e faça perguntas sem precisar escrever SQL ou código.
            </Text>

            <Flex gap="12px" wrap="wrap" mt="32px">
              <Button
                variant="primary"
                size="lg"
                leftIcon={<Upload size={19} strokeWidth={1.8} />}
                onClick={() => navigate('/upload')}
              >
                Carregar arquivo ZIP
              </Button>
              <Button
                as={ChakraLink}
                href="#como-funciona"
                variant="secondary"
                size="lg"
                px="20px"
                color="text.primary"
                _hover={{ textDecoration: 'none', bg: 'background.subtle', color: 'text.primary' }}
              >
                Conhecer o fluxo
              </Button>
            </Flex>

            <Text mt="26px" fontSize="13.5px" color="text.muted">
              Múltiplos CSVs · Dicionário de dados · Histórico de consultas
            </Text>
          </Box>

          <AppPreview />
        </Grid>
      </PageContainer>

      {/* Como funciona */}
      <Box
        as="section"
        id="como-funciona"
        py={{ base: '48px', lg: '64px' }}
        px={pageGutter}
        bg="background.surface"
        borderTopWidth="1px"
        borderBottomWidth="1px"
        borderStyle="solid"
        borderColor="border.default"
      >
        <Box maxW="1320px" mx="auto">
          <Heading as="h2" size="h2" m={0}>
            Como funciona
          </Heading>
          <Text mt="10px" fontSize="16px" color="text.muted">
            Quatro passos entre o arquivo bruto e a primeira resposta.
          </Text>

          <Grid
            templateColumns={{
              base: '1fr',
              sm: 'repeat(2, minmax(0, 1fr))',
              lg: 'repeat(4, minmax(0, 1fr))',
            }}
            gap="20px"
            mt="36px"
          >
            {STEPS.map((step) => (
              <SurfaceCard key={step.number} tone="muted" elevated={false} p="26px">
                <Box
                  as="span"
                  display="grid"
                  placeItems="center"
                  width="38px"
                  height="38px"
                  borderRadius="lg"
                  bg="brand.primary"
                  fontSize="14px"
                  fontWeight={700}
                  color="#111111"
                >
                  {step.number}
                </Box>
                <Heading as="h3" mt="18px" mb="8px" fontSize="18px" fontWeight={600}>
                  {step.title}
                </Heading>
                <Text m={0} fontSize="14.5px" lineHeight={1.6} color="text.muted">
                  {step.description}
                </Text>
              </SurfaceCard>
            ))}
          </Grid>
        </Box>
      </Box>

      {/* Recursos */}
      <PageContainer as="section" py={{ base: '48px', lg: '64px' }}>
        <Heading as="h2" size="h2" m={0}>
          Recursos
        </Heading>

        <Grid
          templateColumns={{
            base: '1fr',
            sm: 'repeat(2, minmax(0, 1fr))',
            lg: 'repeat(3, minmax(0, 1fr))',
          }}
          gap="20px"
          mt="32px"
        >
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <SurfaceCard key={feature.title} p="24px">
                <Box as="span" color="brand.primaryHover">
                  <Icon size={22} strokeWidth={1.8} />
                </Box>
                <Heading as="h3" mt="14px" mb="6px" fontSize="17px" fontWeight={600}>
                  {feature.title}
                </Heading>
                <Text m={0} fontSize="14.5px" lineHeight={1.6} color="text.muted">
                  {feature.description}
                </Text>
              </SurfaceCard>
            );
          })}
        </Grid>
      </PageContainer>

      {/* CTA final */}
      <PageContainer as="section" pb={{ base: '56px', lg: '72px' }}>
        <Flex
          align="center"
          justify="space-between"
          gap="28px"
          wrap="wrap"
          p={{ base: '32px', lg: '48px' }}
          borderRadius="3xl"
          bg="background.inverse"
          borderWidth="1px"
          borderStyle="solid"
          borderColor="border.strong"
        >
          <Box>
            <Heading as="h2" size="h2" m={0} color="text.onInverse">
              Pronto para consultar seus dados?
            </Heading>
            <Text mt="10px" fontSize="16px" color="text.onInverseMuted">
              Carregue um ZIP e faça a primeira pergunta em menos de um minuto.
            </Text>
          </Box>
          <Button variant="primary" size="lg" px="26px" onClick={() => navigate('/upload')}>
            Começar agora
          </Button>
        </Flex>
      </PageContainer>

      {/* Rodapé */}
      <Flex
        as="footer"
        align="center"
        justify="space-between"
        gap="16px"
        wrap="wrap"
        px={pageGutter}
        py="24px"
        borderTopWidth="1px"
        borderTopStyle="solid"
        borderColor="border.default"
      >
        <Text m={0} fontSize="13px" color="text.muted">
          CSV Insight · Consulta de dados em linguagem natural
        </Text>
        <Text m={0} fontSize="13px" color="text.muted">
          Documentação · Privacidade · Suporte
        </Text>
      </Flex>
    </Box>
  );
}

export default HomePage;
