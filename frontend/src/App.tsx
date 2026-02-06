import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import CampaignPage from './pages/CampaignPage';
import SessionPage from './pages/SessionPage';
import CharactersPage from './pages/CharactersPage';
import WorldPage from './pages/WorldPage';
import KnowledgePage from './pages/KnowledgePage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="campaigns/:campaignId" element={<CampaignPage />} />
        <Route path="sessions/:sessionId" element={<SessionPage />} />
        <Route path="campaigns/:campaignId/characters" element={<CharactersPage />} />
        <Route path="campaigns/:campaignId/world" element={<WorldPage />} />
        <Route path="campaigns/:campaignId/knowledge" element={<KnowledgePage />} />
      </Route>
    </Routes>
  );
}

export default App;
