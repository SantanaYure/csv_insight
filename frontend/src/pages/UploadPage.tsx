import { Box, Button, Flex, Heading, Text } from '@chakra-ui/react';
import { zodResolver } from '@hookform/resolvers/zod';
import { AlertCircle, ArrowRight } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { PageContainer } from '../components/common/PageContainer';
import { SurfaceCard } from '../components/common/SurfaceCard';
import { FileDropzone } from '../components/upload/FileDropzone';
import { SelectedFileCard } from '../components/upload/SelectedFileCard';
import { useUploadDataset } from '../hooks/useUploadDataset';
import { ProcessingView } from './ProcessingView';

const MAX_FILE_SIZE = 200 * 1024 * 1024;

const uploadSchema = z.object({
  file: z
    .instanceof(File, { message: 'Selecione um arquivo para continuar.' })
    .refine((file) => /\.(csv|zip)$/i.test(file.name), {
      message: 'Envie um arquivo .csv ou .zip.',
    })
    .refine((file) => file.size <= MAX_FILE_SIZE, {
      message: 'O arquivo excede o tamanho máximo de 200 MB.',
    })
    .refine((file) => file.size > 0, { message: 'O arquivo enviado está vazio.' }),
});

type UploadFormValues = z.infer<typeof uploadSchema>;

interface UploadLocationState {
  reason?: 'missing-dataset';
}

export function UploadPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const upload = useUploadDataset();

  const missingDataset =
    (location.state as UploadLocationState | null)?.reason === 'missing-dataset';

  const {
    handleSubmit,
    setValue,
    resetField,
    formState: { errors },
  } = useForm<UploadFormValues>({
    resolver: zodResolver(uploadSchema),
    mode: 'onChange',
  });

  useEffect(() => {
    if (upload.status === 'success' && upload.dataset) {
      const timer = window.setTimeout(() => navigate(`/datasets/${upload.dataset?.id}`), 400);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [navigate, upload.dataset, upload.status]);

  const handleSelectFile = (file: File) => {
    setValue('file', file, { shouldValidate: true });
    const parsed = uploadSchema.safeParse({ file });
    if (parsed.success) {
      upload.selectFile(file);
    } else {
      upload.removeFile();
    }
  };

  const handleRemove = () => {
    resetField('file');
    upload.removeFile();
  };

  const onSubmit = handleSubmit(() => upload.start());

  const isUploading = upload.status === 'uploading';
  const validationMessage = errors.file?.message;

  // O envio acontece na própria tela de upload; o processamento tem tela própria.
  if (upload.status === 'processing' || upload.status === 'success' || upload.status === 'error') {
    return (
      <ProcessingView
        fileName={upload.file?.name ?? 'dados.csv'}
        status={upload.status}
        processingProgress={upload.processingProgress}
        steps={upload.steps}
        completedSteps={upload.completedSteps}
        error={upload.error}
        onRetry={upload.start}
        onChooseAnother={handleRemove}
      />
    );
  }

  return (
    <PageContainer
      maxContentWidth="760px"
      pt={{ base: '40px', lg: '56px' }}
      pb={{ base: '56px', lg: '72px' }}
    >
      <Flex as="nav" align="center" gap="8px" fontSize="13px" color="text.muted" aria-label="Trilha de navegação">
        <Box
          as="button"
          type="button"
          onClick={() => navigate('/')}
          bg="none"
          border={0}
          p={0}
          fontSize="13px"
          color="text.muted"
          cursor="pointer"
          _hover={{ color: 'text.primary' }}
        >
          Início
        </Box>
        <Box as="span">/</Box>
        <Box as="span" color="text.primary" fontWeight={500}>
          Upload
        </Box>
      </Flex>

      <Heading as="h1" size="h1" mt="18px">
        Envie seu conjunto de dados
      </Heading>
      <Text mt="12px" fontSize="17px" lineHeight={1.6} color="text.muted">
        Envie um CSV ou um ZIP com um ou mais CSVs. O dicionário de dados é opcional.
      </Text>

      {missingDataset ? (
        <Flex
          role="status"
          gap="12px"
          mt="24px"
          px="16px"
          py="14px"
          borderRadius="xl"
          bg="brand.tint"
          borderWidth="1px"
          borderStyle="solid"
          borderColor="brand.soft"
        >
          <Box as="span" flex="none" mt="1px" color="brand.primaryHover">
            <AlertCircle size={20} strokeWidth={1.9} />
          </Box>
          <Text m={0} fontSize="14px" lineHeight={1.55} color="text.secondary">
            Nenhum conjunto de dados está carregado nesta sessão. Envie um CSV ou ZIP para
            liberar o resumo, a consulta e o histórico.
          </Text>
        </Flex>
      ) : null}

      <SurfaceCard as="form" onSubmit={onSubmit} mt="32px" p="26px" display="block">
        {validationMessage ? (
          <Flex
            role="alert"
            gap="12px"
            mb="20px"
            px="16px"
            py="14px"
            borderRadius="xl"
            bg="background.subtle"
            borderWidth="1px"
            borderStyle="solid"
            borderColor="border.strong"
            borderLeftWidth="3px"
            borderLeftColor="feedback.error"
          >
            <Box as="span" flex="none" mt="1px" color="feedback.error">
              <AlertCircle size={20} strokeWidth={1.9} />
            </Box>
            <Box>
              <Text m={0} fontSize="14.5px" fontWeight={600} color="text.primary">
                Arquivo inválido
              </Text>
              <Text mt="4px" fontSize="14px" lineHeight={1.55} color="text.muted">
                {validationMessage} Envie um arquivo .csv ou .zip de até 200 MB.
              </Text>
            </Box>
          </Flex>
        ) : null}

        <FileDropzone onSelectFile={handleSelectFile} isDisabled={isUploading} />

        {upload.file ? (
          <SelectedFileCard
            file={upload.file}
            uploadProgress={upload.uploadProgress}
            isUploading={isUploading}
            onRemove={handleRemove}
          />
        ) : null}

        <Flex gap="10px" wrap="wrap" mt="22px">
          {isUploading ? (
            <>
              <Button variant="primary" isDisabled isLoading loadingText="Enviando arquivo…" />
              <Button variant="secondary" onClick={handleRemove}>
                Cancelar
              </Button>
            </>
          ) : upload.file ? (
            <>
              <Button type="submit" variant="primary" rightIcon={<ArrowRight size={17} strokeWidth={2} />}>
                Processar arquivo
              </Button>
              <Button variant="secondary" onClick={handleRemove}>
                Remover
              </Button>
            </>
          ) : (
            <>
              <Button type="submit" variant="primary" isDisabled>
                Processar arquivo
              </Button>
              <Text alignSelf="center" fontSize="13.5px" color="text.muted">
                Selecione um arquivo para continuar
              </Text>
            </>
          )}
        </Flex>
      </SurfaceCard>

      <SurfaceCard mt="20px" px="26px" py="24px" elevated={false}>
        <Heading as="h2" m={0} fontSize="17px" fontWeight={600}>
          Estrutura esperada do arquivo
        </Heading>
        <Box
          mt="14px"
          px="18px"
          py="16px"
          borderRadius="lg"
          bg="background.subtle"
          borderWidth="1px"
          borderStyle="solid"
          borderColor="border.default"
          fontFamily="mono"
          fontSize="13.5px"
          lineHeight={2}
          color="text.secondary"
        >
          <Box color="text.primary" fontWeight={500}>
            dados.zip ou dados.csv
          </Box>
          <Box>├─ tabela_1.csv</Box>
          <Box>├─ tabela_2.csv</Box>
          <Box>└─ dicionario_dados.csv (opcional)</Box>
        </Box>
        <Text mt="14px" fontSize="14px" lineHeight={1.6} color="text.muted">
          O sistema aceita qualquer estrutura de colunas. Se existir, o dicionário descreve cada coluna com <Text as="span" fontFamily="mono">arquivo</Text>,{' '}
          <Text as="span" fontFamily="mono">coluna</Text>, <Text as="span" fontFamily="mono">tipo</Text>{' '}
          e <Text as="span" fontFamily="mono">descricao</Text>. Ele é opcional: sem o dicionário, os
          tipos das colunas são inferidos a partir dos próprios valores.
        </Text>
      </SurfaceCard>
    </PageContainer>
  );
}

export default UploadPage;
