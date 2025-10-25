
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { store } from './store/store';
import { theme } from './theme/enterpriseTheme';
import { AuthProvider } from './providers/AuthProvider';
import { SocketProvider } from './providers/SocketProvider';
import AppRouter from './components/AppRouter';
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <ErrorBoundary>
          <BrowserRouter>
            <AuthProvider>
              <SocketProvider>
                <AppRouter />
              </SocketProvider>
            </AuthProvider>
          </BrowserRouter>
        </ErrorBoundary>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
