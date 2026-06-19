import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom';
import { I18nProvider } from '@/i18n/context';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import ProjectFiles from '@/pages/ProjectFiles';
import ObjectList from '@/pages/ObjectList';
import ObjectDetail from '@/pages/ObjectDetail';
import Changelog from '@/pages/Changelog';

function AppRoutes() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/project-files" element={<ProjectFiles />} />
        <Route path="/objects/:type" element={<ObjectList />} />
        <Route path="/objects/:type/:id" element={<ObjectDetail />} />
        <Route path="/changelog" element={<Changelog />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <I18nProvider>
        <AppRoutes />
      </I18nProvider>
    </BrowserRouter>
  );
}
