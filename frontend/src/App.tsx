import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ConfigProvider } from 'antd';
import ruRU from 'antd/locale/ru_RU';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { MainLayout } from './components/layout/MainLayout';
import { Today } from './pages/Today';
import { PatientsList } from './pages/Patients/PatientsList';
import { PatientCard } from './pages/Patients/PatientCard';
import { PatientForm } from './pages/Patients/PatientForm';
import { CyclesList } from './pages/Cycles/CyclesList';
import { LabPage } from './pages/Lab/LabPage';
import { EmbryosList } from './pages/Embryos/EmbryosList';
import { DocumentsList } from './pages/Documents/DocumentsList';
import { TeamPage } from './pages/Team/TeamPage';
import { SettingsPage } from './pages/Settings/SettingsPage';

import './i18n';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Ant Design theme configuration based on EMBICO design
const theme = {
  token: {
    colorPrimary: '#004598',
    colorLink: '#004598',
    colorSuccess: '#276b55',
    colorWarning: '#8c5c23',
    colorError: '#a13f41',
    borderRadius: 5,
    fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif',
  },
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={ruRU} theme={theme}>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Navigate to="/today" replace />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <MainLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/today" replace />} />
                <Route path="today" element={<Today />} />
                <Route path="patients" element={<PatientsList />} />
                <Route path="patients/new" element={<PatientForm />} />
                <Route path="patients/:id" element={<PatientCard />} />
                <Route path="patients/:id/edit" element={<PatientForm />} />
                <Route path="cycles" element={<CyclesList />} />
                <Route path="lab" element={<LabPage />} />
                <Route path="embryos" element={<EmbryosList />} />
                <Route path="documents" element={<DocumentsList />} />
                <Route path="team" element={<TeamPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ConfigProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
