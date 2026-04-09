import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Importation des pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import TableOfContents from './pages/TableOfContents';
import TagsIdeasPage from './pages/TagsIdeasPage';
import Navbar from './components/Navbar';
import BooksPage from './pages/BooksPage';
import AdminPage from './pages/AdminPage';
import { BookProvider } from './contexts/BookContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/" />;
};

const AdminRoute = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) return <Navigate to="/" />;
  if (!user?.is_admin) return <Navigate to="/dashboard" />;
  return children;
};

function AppRoutes() {
  return (
    <div className="pt-20 p-4"> {/* pt-20 laisse de la place sous la Navbar */}
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
          <Routes>
            {/* Route par défaut : Connexion */}
            <Route path="/" element={<Login />} />

            {/* Routes protégées */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/table-of-contents"
              element={
                <ProtectedRoute>
                  <TableOfContents />
                </ProtectedRoute>
              }
            />

            <Route
              path="/tags-ideas"
              element={
                <ProtectedRoute>
                  <TagsIdeasPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/books"
              element={
                <ProtectedRoute>
                  <BooksPage />
                </ProtectedRoute>
              }
            />

            {/* Route admin */}
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminPage />
                </AdminRoute>
              }
            />

            {/* Redirection si l'URL n'existe pas */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <BookProvider>
          <AppRoutes />
        </BookProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
