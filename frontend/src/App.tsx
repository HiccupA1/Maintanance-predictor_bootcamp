import { BrowserRouter } from 'react-router-dom';

import { AppRoutes } from './routes/AppRoutes';

// PUBLIC_INTERFACE
export default function App() {
  /** Root application component providing the router context. */
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
