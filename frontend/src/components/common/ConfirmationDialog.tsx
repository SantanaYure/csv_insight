import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
} from '@chakra-ui/react';
import { useRef } from 'react';

interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  /** `danger` pinta o botão de confirmação com a cor de erro. */
  tone?: 'brand' | 'danger';
  isLoading?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

/** Diálogo de confirmação com foco inicial no botão de cancelar. */
export function ConfirmationDialog({
  isOpen,
  title,
  description,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  tone = 'brand',
  isLoading = false,
  onCancel,
  onConfirm,
}: ConfirmationDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onCancel}
      isCentered
      initialFocusRef={cancelRef}
      size="md"
      motionPreset="slideInBottom"
    >
      <ModalOverlay />
      <ModalContent maxW="440px" mx="24px">
        <ModalHeader>{title}</ModalHeader>
        <ModalBody>
          <Text fontSize="15px" lineHeight={1.6} color="text.muted">
            {description}
          </Text>
        </ModalBody>
        <ModalFooter justifyContent="flex-end">
          <Button ref={cancelRef} variant="secondary" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button
            variant="primary"
            onClick={onConfirm}
            isLoading={isLoading}
            bg={tone === 'danger' ? 'feedback.error' : undefined}
            borderColor={tone === 'danger' ? 'feedback.error' : undefined}
            color={tone === 'danger' ? '#FFFFFF' : undefined}
            _hover={tone === 'danger' ? { bg: '#A93226' } : undefined}
          >
            {confirmLabel}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
