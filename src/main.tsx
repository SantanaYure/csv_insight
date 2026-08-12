import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { App } from './app/App';

const container = document.getElementById('root');

if (!container) {
  throw new Error('Elemento #root não encontrado no documento.');
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
