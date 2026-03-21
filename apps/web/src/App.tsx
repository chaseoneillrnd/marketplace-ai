import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, useT } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { FlagsProvider } from './context/FlagsContext';
import { Nav } from './components/Nav';
import { AuthModal } from './components/AuthModal';
import { HomeView } from './views/HomeView';
import { BrowseView } from './views/BrowseView';
import { SearchView } from './views/SearchView';
import { FilteredView } from './views/FilteredView';
import { SkillDetailView } from './views/SkillDetailView';

function AppShell() {
  const C = useT();
  const [showAuth, setShowAuth] = useState(false);

  return (
    <div
      style={{
        background: C.bg,
        minHeight: '100vh',
        color: C.text,
        fontFamily: "'Outfit',sans-serif",
        transition: 'background 0.3s, color 0.3s',
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
        *, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
        ::-webkit-scrollbar { width:4px; height:4px; }
        ::-webkit-scrollbar-thumb { background:${C.scrollThumb}; border-radius:2px; }
        input, textarea { transition: background 0.3s, border-color 0.2s; }
        input::placeholder, textarea::placeholder { color:${C.dim}; }
      `}</style>

      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}

      <Nav onAuthOpen={() => setShowAuth(true)} />

      <div style={{ paddingTop: '60px' }}>
        <Routes>
          <Route path="/" element={<HomeView />} />
          <Route path="/browse" element={<BrowseView />} />
          <Route path="/search" element={<SearchView />} />
          <Route path="/filtered" element={<FilteredView />} />
          <Route path="/skills/:slug" element={<SkillDetailView />} />
        </Routes>
      </div>
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <FlagsProvider>
            <AppShell />
          </FlagsProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
