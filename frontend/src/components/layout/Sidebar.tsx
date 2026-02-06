import { Link, useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  UserCircle,
  ScrollText,
  Map,
  BookOpen,
  ChevronRight,
  Heart,
  Swords,
} from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';
import { useGameStore } from '../../stores/gameStore';
import { clsx } from 'clsx';

type SidebarTab = 'party' | 'npcs' | 'quests' | 'map' | 'lore';

const tabs: { id: SidebarTab; label: string; icon: React.ReactNode }[] = [
  { id: 'party', label: 'Party', icon: <Users className="w-5 h-5" /> },
  { id: 'npcs', label: 'NPCs', icon: <UserCircle className="w-5 h-5" /> },
  { id: 'quests', label: 'Quests', icon: <ScrollText className="w-5 h-5" /> },
  { id: 'map', label: 'Map', icon: <Map className="w-5 h-5" /> },
  { id: 'lore', label: 'Lore', icon: <BookOpen className="w-5 h-5" /> },
];

export default function Sidebar() {
  const { campaignId } = useParams();
  const { isSidebarOpen, sidebarTab, setSidebarTab } = useUIStore();
  const { partyMembers, currentCampaign } = useGameStore();

  return (
    <AnimatePresence>
      {isSidebarOpen && (
        <motion.aside
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 280, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="bg-background-secondary border-r border-primary/20 flex flex-col overflow-hidden"
        >
          {/* Tab buttons */}
          <div className="flex border-b border-primary/20">
            {tabs.slice(0, 3).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSidebarTab(tab.id)}
                className={clsx(
                  'flex-1 p-3 flex flex-col items-center gap-1 transition-colors',
                  sidebarTab === tab.id
                    ? 'text-primary bg-background-tertiary'
                    : 'text-text-muted hover:text-text hover:bg-background-tertiary/50'
                )}
              >
                {tab.icon}
                <span className="text-xs">{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto p-4">
            {sidebarTab === 'party' && (
              <PartyTab partyMembers={partyMembers} campaignId={campaignId} />
            )}
            {sidebarTab === 'npcs' && <NPCsTab campaignId={campaignId} />}
            {sidebarTab === 'quests' && <QuestsTab />}
            {sidebarTab === 'map' && <MapTab campaignId={campaignId} />}
            {sidebarTab === 'lore' && <LoreTab campaignId={campaignId} />}
          </div>

          {/* Bottom navigation */}
          <div className="p-2 border-t border-primary/20 flex gap-1">
            {tabs.slice(3).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSidebarTab(tab.id)}
                className={clsx(
                  'flex-1 p-2 flex items-center justify-center gap-2 rounded transition-colors',
                  sidebarTab === tab.id
                    ? 'text-primary bg-background-tertiary'
                    : 'text-text-muted hover:text-text hover:bg-background-tertiary/50'
                )}
              >
                {tab.icon}
                <span className="text-sm">{tab.label}</span>
              </button>
            ))}
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

// Party Tab Component
function PartyTab({ partyMembers, campaignId }: { partyMembers: any[]; campaignId?: string }) {
  if (partyMembers.length === 0) {
    return (
      <div className="text-center text-text-muted py-8">
        <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No party members yet</p>
        {campaignId && (
          <Link
            to={`/campaigns/${campaignId}/characters`}
            className="text-primary hover:underline mt-2 inline-block"
          >
            Add characters
          </Link>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {partyMembers.map((char) => (
        <div
          key={char.id}
          className="p-3 bg-background-tertiary rounded-lg border border-primary/10 hover:border-primary/30 transition-colors cursor-pointer"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-heading text-primary">{char.name}</span>
            <span className="text-xs text-text-muted">Lv. {char.level}</span>
          </div>
          <div className="text-sm text-text-muted mb-2">
            {char.race} {char.char_class}
          </div>
          {/* HP Bar */}
          <div className="flex items-center gap-2">
            <Heart className="w-4 h-4 text-danger" />
            <div className="flex-1 h-2 bg-background rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-danger to-red-400"
                style={{ width: `${(char.hp_current / char.hp_max) * 100}%` }}
              />
            </div>
            <span className="text-xs font-mono text-text-muted">
              {char.hp_current}/{char.hp_max}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

// NPCs Tab Component
function NPCsTab({ campaignId }: { campaignId?: string }) {
  return (
    <div className="text-center text-text-muted py-8">
      <UserCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
      <p>NPCs you've met will appear here</p>
    </div>
  );
}

// Quests Tab Component
function QuestsTab() {
  return (
    <div className="text-center text-text-muted py-8">
      <ScrollText className="w-12 h-12 mx-auto mb-4 opacity-50" />
      <p>No active quests</p>
    </div>
  );
}

// Map Tab Component
function MapTab({ campaignId }: { campaignId?: string }) {
  return (
    <div className="text-center text-text-muted py-8">
      <Map className="w-12 h-12 mx-auto mb-4 opacity-50" />
      <p>Explore to discover locations</p>
      {campaignId && (
        <Link
          to={`/campaigns/${campaignId}/world`}
          className="text-primary hover:underline mt-2 inline-flex items-center gap-1"
        >
          View world map <ChevronRight className="w-4 h-4" />
        </Link>
      )}
    </div>
  );
}

// Lore Tab Component
function LoreTab({ campaignId }: { campaignId?: string }) {
  return (
    <div className="text-center text-text-muted py-8">
      <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
      <p>Discovered lore will appear here</p>
      {campaignId && (
        <Link
          to={`/campaigns/${campaignId}/knowledge`}
          className="text-primary hover:underline mt-2 inline-flex items-center gap-1"
        >
          Knowledge graph <ChevronRight className="w-4 h-4" />
        </Link>
      )}
    </div>
  );
}
