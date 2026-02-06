import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'dark' | 'light';
type SidebarTab = 'party' | 'npcs' | 'quests' | 'map' | 'lore';
type RightPanelTab = 'characters' | 'location' | 'encounter' | 'knowledge';

interface ModalState {
  isOpen: boolean;
  type: string | null;
  data?: unknown;
}

interface UIState {
  // Theme
  theme: Theme;

  // Sidebar
  isSidebarOpen: boolean;
  sidebarTab: SidebarTab;

  // Right panel
  isRightPanelOpen: boolean;
  rightPanelTab: RightPanelTab;

  // Modals
  modal: ModalState;

  // Dice roller
  isDiceRollerOpen: boolean;

  // Notifications
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'info' | 'warning';
    message: string;
    duration?: number;
  }>;

  // Actions
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setSidebarTab: (tab: SidebarTab) => void;
  toggleRightPanel: () => void;
  setRightPanelTab: (tab: RightPanelTab) => void;
  openModal: (type: string, data?: unknown) => void;
  closeModal: () => void;
  toggleDiceRoller: () => void;
  addNotification: (notification: Omit<UIState['notifications'][0], 'id'>) => void;
  removeNotification: (id: string) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Initial state
      theme: 'dark',
      isSidebarOpen: true,
      sidebarTab: 'party',
      isRightPanelOpen: true,
      rightPanelTab: 'characters',
      modal: { isOpen: false, type: null },
      isDiceRollerOpen: false,
      notifications: [],

      // Actions
      setTheme: (theme) => set({ theme }),

      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

      setSidebarTab: (tab) => set({ sidebarTab: tab, isSidebarOpen: true }),

      toggleRightPanel: () => set((state) => ({ isRightPanelOpen: !state.isRightPanelOpen })),

      setRightPanelTab: (tab) => set({ rightPanelTab: tab, isRightPanelOpen: true }),

      openModal: (type, data) => set({ modal: { isOpen: true, type, data } }),

      closeModal: () => set({ modal: { isOpen: false, type: null, data: undefined } }),

      toggleDiceRoller: () => set((state) => ({ isDiceRollerOpen: !state.isDiceRollerOpen })),

      addNotification: (notification) =>
        set((state) => ({
          notifications: [
            ...state.notifications,
            { ...notification, id: `${Date.now()}-${Math.random()}` },
          ],
        })),

      removeNotification: (id) =>
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),
    }),
    {
      name: 'lorekeeper-ui',
      partialize: (state) => ({
        theme: state.theme,
        isSidebarOpen: state.isSidebarOpen,
        isRightPanelOpen: state.isRightPanelOpen,
      }),
    }
  )
);

// Selectors
export const selectTheme = (state: UIState) => state.theme;
export const selectIsSidebarOpen = (state: UIState) => state.isSidebarOpen;
export const selectSidebarTab = (state: UIState) => state.sidebarTab;
export const selectIsRightPanelOpen = (state: UIState) => state.isRightPanelOpen;
export const selectRightPanelTab = (state: UIState) => state.rightPanelTab;
export const selectModal = (state: UIState) => state.modal;
export const selectIsDiceRollerOpen = (state: UIState) => state.isDiceRollerOpen;
export const selectNotifications = (state: UIState) => state.notifications;
