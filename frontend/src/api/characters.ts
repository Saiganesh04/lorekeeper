import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { Character, CharacterCreate } from '../types';

// Query keys
export const characterKeys = {
  all: ['characters'] as const,
  lists: () => [...characterKeys.all, 'list'] as const,
  listByCampaign: (campaignId: string, filters?: { type?: string; aliveOnly?: boolean }) =>
    [...characterKeys.lists(), { campaignId, ...filters }] as const,
  details: () => [...characterKeys.all, 'detail'] as const,
  detail: (id: string) => [...characterKeys.details(), id] as const,
};

// API functions
export async function fetchCharacters(
  campaignId: string,
  options?: { type?: string; aliveOnly?: boolean }
): Promise<{ characters: Character[]; total: number }> {
  const { data } = await apiClient.get(`/campaigns/${campaignId}/characters`, {
    params: {
      character_type: options?.type,
      alive_only: options?.aliveOnly ?? true,
    },
  });
  return data;
}

export async function fetchCharacter(id: string): Promise<Character> {
  const { data } = await apiClient.get(`/characters/${id}`);
  return data;
}

export async function createCharacter(campaignId: string, character: CharacterCreate): Promise<Character> {
  const { data } = await apiClient.post(`/campaigns/${campaignId}/characters`, character);
  return data;
}

export async function createNPC(
  campaignId: string,
  options: {
    name?: string;
    role?: string;
    locationId?: string;
    personalityHints?: string[];
    generateWithAI?: boolean;
  }
): Promise<Character> {
  const { data } = await apiClient.post(`/campaigns/${campaignId}/npcs`, {
    name: options.name,
    role: options.role,
    location_id: options.locationId,
    personality_hints: options.personalityHints,
    generate_with_ai: options.generateWithAI ?? true,
  });
  return data;
}

export async function updateCharacter(id: string, updates: Partial<CharacterCreate>): Promise<Character> {
  const { data } = await apiClient.put(`/characters/${id}`, updates);
  return data;
}

export async function deleteCharacter(id: string): Promise<void> {
  await apiClient.delete(`/characters/${id}`);
}

export async function chatWithNPC(
  characterId: string,
  message: string,
  context?: string
): Promise<{
  character_id: string;
  character_name: string;
  dialogue: string;
  mood: string;
  disposition_change: number;
  revealed_information: string[] | null;
}> {
  const { data } = await apiClient.post(`/characters/${characterId}/dialogue`, {
    message,
    context,
  });
  return data;
}

// Hooks
export function useCharacters(campaignId: string, options?: { type?: string; aliveOnly?: boolean }) {
  return useQuery({
    queryKey: characterKeys.listByCampaign(campaignId, options),
    queryFn: () => fetchCharacters(campaignId, options),
    enabled: !!campaignId,
  });
}

export function useCharacter(id: string) {
  return useQuery({
    queryKey: characterKeys.detail(id),
    queryFn: () => fetchCharacter(id),
    enabled: !!id,
  });
}

export function useCreateCharacter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ campaignId, character }: { campaignId: string; character: CharacterCreate }) =>
      createCharacter(campaignId, character),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: characterKeys.listByCampaign(data.campaign_id) });
    },
  });
}

export function useCreateNPC() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      campaignId,
      options,
    }: {
      campaignId: string;
      options: {
        name?: string;
        role?: string;
        locationId?: string;
        personalityHints?: string[];
        generateWithAI?: boolean;
      };
    }) => createNPC(campaignId, options),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: characterKeys.listByCampaign(data.campaign_id) });
    },
  });
}

export function useUpdateCharacter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<CharacterCreate> }) =>
      updateCharacter(id, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: characterKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: characterKeys.listByCampaign(data.campaign_id) });
    },
  });
}

export function useDeleteCharacter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteCharacter,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: characterKeys.lists() });
    },
  });
}

export function useChatWithNPC() {
  return useMutation({
    mutationFn: ({ characterId, message, context }: { characterId: string; message: string; context?: string }) =>
      chatWithNPC(characterId, message, context),
  });
}
