import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { Encounter } from '../types';

// Query keys
export const encounterKeys = {
  all: ['encounters'] as const,
  details: () => [...encounterKeys.all, 'detail'] as const,
  detail: (id: string) => [...encounterKeys.details(), id] as const,
};

// API functions
export async function fetchEncounter(id: string): Promise<Encounter> {
  const { data } = await apiClient.get(`/encounters/${id}`);
  return data;
}

export async function createEncounter(
  sessionId: string,
  options: {
    encounterType?: string;
    difficulty?: string;
    locationId?: string;
    theme?: string;
  }
): Promise<Encounter> {
  const { data } = await apiClient.post(`/sessions/${sessionId}/encounters`, {
    encounter_type: options.encounterType || 'combat',
    difficulty: options.difficulty || 'medium',
    location_id: options.locationId,
    theme: options.theme,
  });
  return data;
}

export async function submitEncounterAction(
  encounterId: string,
  action: {
    characterId: string;
    actionType: string;
    targetId?: string;
    description?: string;
  }
): Promise<{
  encounter_id: string;
  action_result: {
    success: boolean;
    description: string;
    damage_dealt: number | null;
    target_defeated: boolean;
    dice_rolls: { type: string; total: number }[];
  };
  narrative: string;
  next_turn: { character_id: string; character_name: string; is_enemy: boolean } | null;
  encounter_status: string;
  enemies_remaining: number;
  round_changed: boolean;
  new_round: number | null;
}> {
  const { data } = await apiClient.post(`/encounters/${encounterId}/action`, {
    character_id: action.characterId,
    action_type: action.actionType,
    target_id: action.targetId,
    description: action.description,
  });
  return data;
}

export async function getBalanceReport(encounterId: string): Promise<{
  encounter_id: string;
  difficulty_rating: string;
  party_power: number;
  enemy_power: number;
  estimated_rounds: number;
  survival_chance: number;
  resource_cost: string;
  recommendations: string[];
}> {
  const { data } = await apiClient.get(`/encounters/${encounterId}/balance`);
  return data;
}

export async function resolveEncounter(
  encounterId: string,
  outcome: 'victory' | 'defeat' | 'fled' | 'negotiated',
  distributeRewards = true
): Promise<{
  encounter_id: string;
  outcome: string;
  rounds_taken: number;
  rewards_distributed: boolean;
  rewards: { xp: number; gold: number; items: string[] } | null;
}> {
  const { data } = await apiClient.post(`/encounters/${encounterId}/resolve`, {
    outcome,
    distribute_rewards: distributeRewards,
  });
  return data;
}

export async function getLoot(encounterId: string): Promise<{
  items: { name: string; type: string; rarity: string; value: number }[];
  gold: number;
  experience: number;
}> {
  const { data } = await apiClient.get(`/encounters/${encounterId}/loot`);
  return data;
}

// Hooks
export function useEncounter(id: string) {
  return useQuery({
    queryKey: encounterKeys.detail(id),
    queryFn: () => fetchEncounter(id),
    enabled: !!id,
    refetchInterval: (data) => (data?.status === 'active' ? 5000 : false), // Refresh every 5s if active
  });
}

export function useCreateEncounter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sessionId,
      options,
    }: {
      sessionId: string;
      options: {
        encounterType?: string;
        difficulty?: string;
        locationId?: string;
        theme?: string;
      };
    }) => createEncounter(sessionId, options),
    onSuccess: (data) => {
      queryClient.setQueryData(encounterKeys.detail(data.id), data);
    },
  });
}

export function useSubmitEncounterAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      encounterId,
      action,
    }: {
      encounterId: string;
      action: {
        characterId: string;
        actionType: string;
        targetId?: string;
        description?: string;
      };
    }) => submitEncounterAction(encounterId, action),
    onSuccess: (data) => {
      // Refetch encounter to get updated state
      queryClient.invalidateQueries({ queryKey: encounterKeys.detail(data.encounter_id) });
    },
  });
}

export function useBalanceReport(encounterId: string) {
  return useQuery({
    queryKey: [...encounterKeys.detail(encounterId), 'balance'],
    queryFn: () => getBalanceReport(encounterId),
    enabled: !!encounterId,
  });
}

export function useResolveEncounter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      encounterId,
      outcome,
      distributeRewards,
    }: {
      encounterId: string;
      outcome: 'victory' | 'defeat' | 'fled' | 'negotiated';
      distributeRewards?: boolean;
    }) => resolveEncounter(encounterId, outcome, distributeRewards),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: encounterKeys.detail(data.encounter_id) });
    },
  });
}

export function useLoot(encounterId: string) {
  return useQuery({
    queryKey: [...encounterKeys.detail(encounterId), 'loot'],
    queryFn: () => getLoot(encounterId),
    enabled: !!encounterId,
  });
}
