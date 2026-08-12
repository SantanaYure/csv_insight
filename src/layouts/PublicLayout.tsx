import { Box, Flex } from '@chakra-ui/react';
import { Outlet } from 'react-router-dom';

import { AppHeader } from '../components/common/AppHeader';

/** Layout das telas públicas: header sticky + conteúdo. */
export function PublicLayout() {
  return (
    <Flex direction="column" minH="100vh" bg="background.page">
      <AppHeader variant="public" />
      <Box as="main" flex="1">
        <Outlet />
      </Box>
    </Flex>
  );
}

export default PublicLayout;
