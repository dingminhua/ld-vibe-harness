import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import ObjectList from "@/pages/ObjectList";
import ObjectDetail from "@/pages/ObjectDetail";
import Validate from "@/pages/Validate";
import Changelog from "@/pages/Changelog";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/objects/:type" element={<ObjectList />} />
          <Route path="/objects/:type/:id" element={<ObjectDetail />} />
          <Route path="/validate" element={<Validate />} />
          <Route path="/changelog" element={<Changelog />} />
        </Route>
      </Routes>
    </Router>
  );
}
