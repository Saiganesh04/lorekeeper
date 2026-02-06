import { create } from 'zustand';
import type { Campaign, GameSession, Character, Encounter, StoryEvent } from '../types';

interface GameState {
  // Current context
  currentCampaign: Campaign | null;
  currentSession: GameSession | null;
  currentEncounter: Encounter | null;

  // Party
  partyMembers: Character[];
  selectedCharacterId: string | null;

  // Story state
  lastStoryEvent: StoryEvent | null;
  isGenerating: boolean;

  // Actions
  setCampaign: (campaign: Campaign | null) => void;
  setSession: (session: GameSession | null) => void;
  setEncounter: (encounter: Encounter | null) => void;
  setPartyMembers: (members: Character[]) => void;
  selectCharacter: (id: string | null) => void;
  setLastStoryEvent: (event: StoryEvent | null) => void;
  setIsGenerating: (isGenerating: boolean) => void;
  updateCharacter: (id: string, updates: Partial<Character>) => void;
  reset: () => void;
}

const initialState = {
  currentCampaign: null,
  currentSession: null,
  currentEncounter: null,
  partyMembers: [],
  selectedCharacterId: null,
  lastStoryEvent: null,
  isGenerating: false,
};

export const useGameStore = create<GameState>((set) => ({
  ...initialState,

  setCampaign: (campaign) => set({ currentCampaign: campaign }),

  setSession: (session) => set({ currentSession: session }),

  setEncounter: (encounter) => set({ currentEncounter: encounter }),

  setPartyMembers: (members) => set({ partyMembers: members }),

  selectCharacter: (id) => set({ selectedCharacterId: id }),

  setLastStoryEvent: (event) => set({ lastStoryEvent: event }),

  setIsGenerating: (isGenerating) => set({ isGenerating }),

  updateCharacter: (id, updates) =>
    set((state) => ({
      partyMembers: state.partyMembers.map((char) =>
        char.id === id ? { ...char, ...updates } : char
      ),
    })),

  reset: () => set(initialState),
}));

// Selectors
export const selectCurrentCampaign = (state: GameState) => state.currentCampaign;
export const selectCurrentSession = (state: GameState) => state.currentSession;
export const selectCurrentEncounter = (state: GameState) => state.currentEncounter;
export const selectPartyMembers = (state: GameState) => state.partyMembers;
export const selectSelectedCharacter = (state: GameState) =>
  state.partyMembers.find((c) => c.id === state.selectedCharacterId);
export const selectIsGenerating = (state: GameState) => state.isGenerating;
