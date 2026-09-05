import { BrowserRouter, Routes, Route } from "react-router-dom";
import { StudentProvider } from "./context/StudentContext";
import Layout from "./components/Layout";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import NewLesson from "./pages/NewLesson";
import TeachingSession from "./pages/TeachingSession";
import Report from "./pages/Report";

export default function App() {
  return (
    <StudentProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Onboarding />} />
          <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
          <Route path="/new-lesson" element={<Layout><NewLesson /></Layout>} />
          <Route path="/session/:lessonId" element={<Layout><TeachingSession /></Layout>} />
          <Route path="/report/:sessionId" element={<Layout><Report /></Layout>} />
        </Routes>
      </BrowserRouter>
    </StudentProvider>
  );
}
