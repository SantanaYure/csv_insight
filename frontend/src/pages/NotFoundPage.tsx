import { Box, Button, Flex, Grid, Heading, Text } from '@chakra-ui/react';
import { X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { PageContainer } from '../components/common/PageContainer';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <PageContainer maxContentWidth="1100px" py={{ base: '56px', lg: '72px' }}>
      <Grid
        templateColumns={{ base: '1fr', lg: '1.05fr .95fr' }}
        gap={{ base: '40px', lg: '56px' }}
        alignItems="center"
      >
        <Box>
          <Text m={0} fontSize="64px" fontWeight={700} letterSpacing="-0.03em" lineHeight={1} color="text.primary">
            404
          </Text>
          <Heading as="h1" size="h1" mt="16px">
            Página não encontrada
          </Heading>
          <Text mt="12px" maxW="46ch" fontSize="17px" lineHeight={1.6} color="text.muted">
            A página que você tentou acessar não existe ou foi removida.
          </Text>

          <Flex gap="12px" wrap="wrap" mt="30px">
            <Button variant="primary" size="lg" onClick={() => navigate('/')}>
              Voltar ao início
            </Button>
            <Button variant="secondary" size="lg" px="20px" onClick={() => navigate('/upload')}>
              Ir para upload
            </Button>
          </Flex>
        </Box>

        <Box
          aria-hidden="true"
          position="relative"
          display="grid"
          gap="14px"
          p="32px"
          bg="background.surface"
          borderWidth="1px"
          borderStyle="solid"
          borderColor="border.default"
          borderRadius="3xl"
          boxShadow="floating"
        >
          <Flex
            align="center"
            gap="12px"
            p="16px"
            borderRadius="xl"
            bg="background.page"
            borderWidth="1px"
            borderStyle="solid"
            borderColor="border.default"
          >
            <Box as="span" flex="none" width="34px" height="34px" borderRadius="9px" bg="brand.primary" />
            <Box flex="1" display="grid" gap="7px">
              <Box as="span" display="block" height="9px" width="70%" borderRadius="full" bg="background.subtle" />
              <Box as="span" display="block" height="9px" width="44%" borderRadius="full" bg="background.subtle" />
            </Box>
          </Flex>

          <Flex
            align="flex-end"
            gap="10px"
            height="110px"
            px="16px"
            py="14px"
            borderRadius="xl"
            bg="background.page"
            borderWidth="1px"
            borderStyle="solid"
            borderColor="border.default"
          >
            <Box flex="1" height="44%" borderRadius="4px 4px 0 0" bg="background.subtle" />
            <Box flex="1" height="72%" borderRadius="4px 4px 0 0" bg="brand.soft" />
            <Box flex="1" height="30%" borderRadius="4px 4px 0 0" bg="background.subtle" />
            <Box flex="1" height="56%" borderRadius="4px 4px 0 0" bg="background.subtle" />
          </Flex>

          <Flex
            align="center"
            gap="12px"
            p="16px"
            borderRadius="xl"
            bg="background.page"
            borderWidth="1px"
            borderStyle="dashed"
            borderColor="border.strong"
          >
            <Box
              as="span"
              flex="none"
              display="grid"
              placeItems="center"
              width="34px"
              height="34px"
              borderRadius="9px"
              bg="background.subtle"
              borderWidth="1px"
              borderStyle="solid"
              borderColor="border.default"
              color="text.muted"
            >
              <X size={17} strokeWidth={2} />
            </Box>
            <Text m={0} fontSize="13.5px" color="text.muted">
              rota inexistente
            </Text>
          </Flex>

          <Box
            as="span"
            position="absolute"
            top="-14px"
            right="-14px"
            display="grid"
            placeItems="center"
            width="52px"
            height="52px"
            borderRadius="2xl"
            bg="brand.primary"
            fontSize="15px"
            fontWeight={700}
            color="#111111"
          >
            ?
          </Box>
        </Box>
      </Grid>
    </PageContainer>
  );
}

export default NotFoundPage;
