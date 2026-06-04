import { BrowserRouter, Routes, Route, useSearchParams } from 'react-router-dom';
import { I18nProvider } from '@/i18n/context';
import Layout from '@/components/Layout';
import TopNavLayout from '@/components/TopNavLayout';
import Dashboard from '@/pages/Dashboard';
import ObjectList from '@/pages/ObjectList';
import ObjectDetail from '@/pages/ObjectDetail';
import Validate from '@/pages/Validate';
import Changelog from '@/pages/Changelog';

function AppRoutes() {
  const [searchParams] = useSearchParams();
  const useTopNav = searchParams.get('layout') === 'topnav';
  const ActiveLayout = useTopNav ? TopNavLayout : Layout;

  return (
    <ActiveLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/objects/:type" element={<ObjectList />} />
        <Route path="/objects/:type/:id" element={<ObjectDetail />} />
        <Route path="/validate" element={<Validate />} />
        <Route path="/changelog" element={<Changelog />} />
      </Routes>
    </ActiveLayout>
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
