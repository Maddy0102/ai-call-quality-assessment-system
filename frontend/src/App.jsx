import { BrowserRouter, Routes, Route } from "react-router-dom";

import DashboardLayout from "./layouts/DashboardLayout";

import Dashboard from "./pages/Dashboard";
import UploadAudio from "./pages/UploadAudio";
import CallHistory from "./pages/CallHistory";
import CallDetails from "./pages/CallDetails";
import Settings from "./pages/Settings";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<UploadAudio />} />
          <Route path="/calls" element={<CallHistory />} />
          <Route path="/calls/:callId" element={<CallDetails />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
