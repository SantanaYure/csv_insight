import { createBrowserRouter, Navigate } from 'react-router-dom';

import { ApplicationLayout } from '../layouts/ApplicationLayout';
import { PublicLayout } from '../layouts/PublicLayout';
import { HomePage } from '../pages/HomePage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { UploadPage } from '../pages/UploadPage';
import { WorkspacePage } from '../pages/WorkspacePage';

export const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/upload', element: <UploadPage /> },
      { path: '/not-found', element: <NotFoundPage /> },
    ],
  },
  {
    path: '/datasets/:datasetId',
    element: <ApplicationLayout />,
    children: [
      { index: true, element: <WorkspacePage /> },
      // Compatibilidade com links antigos das rotas anteriores.
      { path: 'query', element: <Navigate to=".." replace /> },
      { path: 'history', element: <Navigate to="..?panel=history" replace /> },
    ],
  },
  { path: '*', element: <Navigate to="/not-found" replace /> },
]);
