import { lazy, Suspense, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, useT } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { FlagsProvider } from './context/FlagsContext';
import { AnnouncerProvider } from './context/AnnouncerContext';
import { Nav } from './components/Nav';
import { AuthModal } from './components/AuthModal';
import { HomeView } from './views/HomeView';
import { BrowseView } from './views/BrowseView';
import { SearchView } from './views/SearchView';
import { FilteredView } from './views/FilteredView';
import { SkillDetailView } from './views/SkillDetailView';
import { RequireAdmin } from './components/admin/RequireAdmin';
import { AdminLayout } from './components/admin/AdminLayout';
import { AdminLoadingSkeleton } from './components/admin/AdminLoadingSkeleton';

const AdminDashboardView = lazy(() =>
  import('./views/admin/AdminDashboardView').then((m) => ({ default: m.AdminDashboardView })),
);
const AdminQueueView = lazy(() =>
  import('./views/admin/AdminQueueView').then((m) => ({ default: m.AdminQueueView })),
);
const AdminFeedbackView = lazy(() =>
  import('./views/admin/AdminFeedbackView').then((m) => ({ default: m.AdminFeedbackView })),
);
const AdminSkillsView = lazy(() =>
  import('./views/admin/AdminSkillsView').then((m) => ({ default: m.AdminSkillsView })),
);
const AdminRoadmapView = lazy(() =>
  import('./views/admin/AdminRoadmapView').then((m) => ({ default: m.AdminRoadmapView })),
);
const AdminExportView = lazy(() =>
  import('./views/admin/AdminExportView').then((m) => ({ default: m.AdminExportView })),
);

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
      <a
        href="#main-content"
        style={{
          position: 'absolute',
          top: '-40px',
          left: 0,
          background: C.accent,
          color: '#fff',
          padding: '8px 16px',
          borderRadius: '0 0 8px 0',
          fontWeight: 600,
          fontSize: '14px',
          zIndex: 9999,
          transition: 'top 0.15s',
        }}
        onFocus={(e) => { (e.currentTarget as HTMLElement).style.top = '0'; }}
        onBlur={(e) => { (e.currentTarget as HTMLElement).style.top = '-40px'; }}
      >
        Skip to main content
      </a>

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

      <div id="main-content" style={{ paddingTop: '60px' }}>
        <Routes>
          <Route path="/" element={<HomeView />} />
          <Route path="/browse" element={<BrowseView />} />
          <Route path="/search" element={<SearchView />} />
          <Route path="/filtered" element={<FilteredView />} />
          <Route path="/skills/:slug" element={<SkillDetailView />} />

          {/* Admin routes — gated by RequireAdmin */}
          <Route element={<RequireAdmin />}>
            <Route
              path="/admin"
              element={
                <Suspense fallback={<AdminLoadingSkeleton />}>
                  <AdminLayout />
                </Suspense>
              }
            >
              <Route index element={<AdminDashboardView />} />
              <Route path="queue" element={<AdminQueueView />} />
              <Route path="feedback" element={<AdminFeedbackView />} />
              <Route path="skills" element={<AdminSkillsView />} />
              <Route path="roadmap" element={<AdminRoadmapView />} />
              <Route path="export" element={<AdminExportView />} />
            </Route>
          </Route>
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
            <AnnouncerProvider>
              <AppShell />
            </AnnouncerProvider>
          </FlagsProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
