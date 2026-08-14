import {
  Button,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Text,
} from '@chakra-ui/react';
import { Upload } from 'lucide-react';

import type { Dataset } from '../../types/dataset';
import { SidebarDatasetCard, SidebarTableList } from './SidebarPieces';

interface MobileNavigationProps {
  isOpen: boolean;
  onClose: () => void;
  dataset: Dataset;
  onSelectTable: (tableId: string) => void;
  onNewDataset: () => void;
}

/**
 * Drawer de contexto exibido abaixo de `lg`. A troca entre Consulta, Dados
 * e Histórico acontece pelas abas no topo do conteúdo — este menu concentra
 * apenas o dataset, as tabelas e a ação de recomeçar.
 */
export function MobileNavigation({
  isOpen,
  onClose,
  dataset,
  onSelectTable,
  onNewDataset,
}: MobileNavigationProps) {
  return (
    <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
      <DrawerOverlay />
      <DrawerContent maxW="300px" width="80%" px="18px" py="20px">
        <DrawerHeader p={0} fontSize="15px" fontWeight={700} color="text.primary">
          CSV Insight
        </DrawerHeader>
        <DrawerCloseButton
          top="20px"
          right="18px"
          width="40px"
          height="40px"
          borderRadius="10px"
          borderWidth="1px"
          borderStyle="solid"
          borderColor="border.default"
          color="text.primary"
        />

        <DrawerBody p={0} mt="18px" overflowY="auto">
          <SidebarDatasetCard dataset={dataset} compact />

          <Text mt="22px" mb="8px" ml="12px" textStyle="overline" color="text.muted">
            Tabelas
          </Text>
          <SidebarTableList
            dataset={dataset}
            compact
            onSelectTable={(tableId) => {
              onSelectTable(tableId);
              onClose();
            }}
          />

          <Button
            variant="secondary"
            width="100%"
            mt="22px"
            leftIcon={<Upload size={16} strokeWidth={1.8} />}
            onClick={() => {
              onNewDataset();
              onClose();
            }}
          >
            Carregar novo dataset
          </Button>
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  );
}
