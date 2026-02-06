import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { GameSession } from '../types';

// Query keys
export const sessionKeys = {
  all: ['sessions'] as const,
  lists: () => [...sessionKeys.all, 'list'] as const,
  listByCampaign: (campaignId: string) => [...sessionKeys.lists(), { campaignId }] as const,
  details: () => [...sessionKeys.all, 'detail'] as const,
  detail: (id: string) => [...sessionKeys.details(), id] as const,
};

// API functions
export async function fetchSessions(campaignId: string): Promise<{ sessions: GameSession[]; total: number }> {
  const { data } = await apiClient.get(`/campaigns/${campaignId}/sessions`);
  return data;
}

export async function fetchSession(id: string): Promise<GameSession> {
  const { data } = await apiClient.get(`/sessions/${id}`);
  return data;
}

export async function createSession(campaignId: string, notes?: string): Promise<GameSession> {
  const { data } = await apiClient.post(`/campaigns/${campaignId}/sessions`, { notes });
  return data;
}

export async function updateSession(id: string, updates: { status?: string; notes?: string }): Promise<GameSession> {
  const { data } = await apiClient.put(`/sessions/${id}`, updates);
  return data;
}

export async function endSession(id: string, generateRecap: boolean = true): Promise<GameSession> {
  const { data } = await apiClient.post(`/sessions/${id}/end`, { generate_recap: generateRecap });
  return data;
}

// Hooks
export function useSessions(campaignId: string) {
  return useQuery({
    queryKey: sessionKeys.listByCampaign(campaignId),
    queryFn: () => fetchSessions(campaignId),
    enabled: !!campaignId,
  });
}

export function useSession(id: string) {
  return useQuery({
    queryKey: sessionKeys.detail(id),
    queryFn: () => fetchSession(id),
    enabled: !!id,
  });
}

export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ campaignId, notes }: { campaignId: string; notes?: string }) =>
      createSession(campaignId, notes),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.listByCampaign(data.campaign_id) });
    },
  });
}

export function useUpdateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: { status?: string; notes?: string } }) =>
      updateSession(id, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: sessionKeys.listByCampaign(data.campaign_id) });
    },
  });
}

export function useEndSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, generateRecap }: { id: string; generateRecap?: boolean }) =>
      endSession(id, generateRecap),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: sessionKeys.listByCampaign(data.campaign_id) });
    },
  });
}
