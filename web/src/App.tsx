import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { I18nProvider } from '@/i18n/context';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import AttentionTest from '@/pages/AttentionTest';
import ProjectFiles from '@/pages/ProjectFiles';
import ObjectList from '@/pages/ObjectList';
import ObjectDetail from '@/pages/ObjectDetail';
import Validate from '@/pages/Validate';
import Gate from '@/pages/Gate'
import Changelog from '@/pages/Changelog';

function AppRoutes() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/attention-test" element={<AttentionTest />} />
        <Route path="/project-files" element={<ProjectFiles />} />
        <Route path="/objects/:type" element={<ObjectList />} />
        <Route path="/objects/:type/:id" element={<ObjectDetail />} />
        <Route path="/validate" element={<Validate />} />
        <Route path="/gate" element={<Gate />} />
        <Route path="/changelog" element={<Changelog />} />
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
