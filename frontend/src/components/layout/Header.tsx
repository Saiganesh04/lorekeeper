import { Link } from 'react-router-dom';
import { Menu, Settings, Dice6, BookOpen } from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';
import { useGameStore } from '../../stores/gameStore';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

export default function Header() {
  const { toggleSidebar, toggleDiceRoller } = useUIStore();
  const { currentCampaign, currentSession, isGenerating } = useGameStore();

  return (
    <header className="h-14 bg-background-secondary border-b border-primary/20 px-4 flex items-center justify-between">
      {/* Left section */}
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="p-2 text-text-muted hover:text-primary transition-colors rounded hover:bg-background-tertiary"
        >
          <Menu className="w-5 h-5" />
        </button>

        <Link to="/" className="flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-primary" />
          <span className="text-xl font-heading text-primary">Lorekeeper</span>
        </Link>
      </div>

      {/* Center section - Campaign/Session info */}
      <div className="flex items-center gap-4">
        {currentCampaign && (
          <div className="flex items-center gap-2">
            <span className="text-text-muted">Campaign:</span>
            <span className="font-heading text-primary">{currentCampaign.name}</span>
          </div>
        )}
        {currentSession && (
          <div className="flex items-center gap-2">
            <Badge variant="primary">Session {currentSession.session_number}</Badge>
            {currentSession.status === 'active' && (
              <Badge variant="success">Active</Badge>
            )}
          </div>
        )}
        {isGenerating && (
          <Badge variant="info" className="animate-pulse">
            Generating...
          </Badge>
        )}
      </div>

      {/* Right section */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleDiceRoller}
          leftIcon={<Dice6 className="w-4 h-4" />}
        >
          Roll
        </Button>
        <button className="p-2 text-text-muted hover:text-primary transition-colors rounded hover:bg-background-tertiary">
          <Settings className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
