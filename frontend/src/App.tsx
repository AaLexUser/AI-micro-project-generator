import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Sparkles, Zap } from 'lucide-react';
import './index.css';
import { ProjectsPage } from './pages/ProjectsPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-xl border-b border-gray-200/50 shadow-sm">
          <div className="mx-auto max-w-7xl px-6 py-4">
            <div className="flex items-center justify-between">
              <Link
                to="/"
                className="flex items-center gap-3 text-xl font-bold text-gray-900 hover:text-brand-700 transition-colors duration-200"
              >
                <div className="p-2 bg-gradient-to-br from-brand-500 to-brand-600 rounded-xl shadow-lg">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <span className="bg-gradient-to-r from-brand-600 to-brand-800 bg-clip-text text-transparent">
                  AI Micro Project Generator
                </span>
              </Link>

              <nav className="flex items-center gap-6">
                <Link
                  to="/"
                  className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-brand-700 transition-colors duration-200"
                >
                  <Zap className="w-4 h-4" />
                  Projects
                </Link>
              </nav>
            </div>
          </div>
        </header>

        <main className="flex-1 animate-fade-in">
          <Routes>
            <Route path="/" element={<ProjectsPage />} />
            <Route path="/project/:idx" element={<ProjectDetailPage />} />
          </Routes>
        </main>

        <footer className="border-t border-gray-100 bg-gradient-to-r from-gray-50 to-white">
          <div className="mx-auto max-w-7xl px-6 py-8">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Sparkles className="w-4 h-4 text-brand-500" />
                <span>Built with FastAPI + React + AI</span>
              </div>
              <div className="text-xs text-gray-500">
                Crafted with ✨ for learning and exploration
              </div>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
