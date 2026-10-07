import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import "./App.css";

import StudentHome from "./pages/StudentHome";
import ProfessorLogin from "./pages/ProfessorLogin";
import ProfessorDashboard from "./pages/ProfessorDashboard";
import LectureReview from "./pages/LectureReview";


function ProtectedProfessorRoute({ children }) {
  const token = localStorage.getItem("professor_token");

  if (!token) {
    return (
      <Navigate
        to="/professor/login"
        replace
      />
    );
  }

  return children;
}


function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route
          path="/"
          element={<StudentHome />}
        />

        <Route
          path="/professor/login"
          element={<ProfessorLogin />}
        />

        <Route
          path="/professor"
          element={
            <ProtectedProfessorRoute>
              <ProfessorDashboard />
            </ProtectedProfessorRoute>
          }
        />

        <Route
          path="/professor/review"
          element={
            <ProtectedProfessorRoute>
              <LectureReview />
            </ProtectedProfessorRoute>
          }
        />

        <Route
          path="*"
          element={
            <Navigate
              to="/"
              replace
            />
          }
        />

      </Routes>
    </BrowserRouter>
  );
}


export default App;