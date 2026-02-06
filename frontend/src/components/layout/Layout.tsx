import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import { useUIStore } from '../../stores/uiStore';

export default function Layout() {
  const { isDiceRollerOpen, toggleDiceRoller } = useUIStore();

  return (
    <div className="h-screen flex flex-col bg-background">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {/* Dice Roller Modal would go here */}
    </div>
  );
}
