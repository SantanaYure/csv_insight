import { apiDataService } from './apiDataService';
import type { DataService } from './DataService';
import { mockDataService } from './mockDataService';

/**
 * Seletor de implementação. Com `VITE_USE_MOCKS=true` a aplicação roda
 * inteiramente com dados simulados; caso contrário usa o backend real.
 */
export const dataService: DataService =
  import.meta.env.VITE_USE_MOCKS === 'true' ? mockDataService : apiDataService;

export type { DataService };
export { apiDataService, mockDataService };
