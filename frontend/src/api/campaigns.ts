import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { Campaign, CampaignCreate } from '../types';

// Query keys
export const campaignKeys = {
  all: ['campaigns'] as const,
  lists: () => [...campaignKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...campaignKeys.lists(), filters] as const,
  details: () => [...campaignKeys.all, 'detail'] as const,
  detail: (id: string) => [...campaignKeys.details(), id] as const,
};

// API functions
export async function fetchCampaigns(): Promise<{ campaigns: Campaign[]; total: number }> {
  const { data } = await apiClient.get('/campaigns');
  return data;
}

export async function fetchCampaign(id: string): Promise<Campaign> {
  const { data } = await apiClient.get(`/campaigns/${id}`);
  return data;
}

export async function createCampaign(campaign: CampaignCreate): Promise<Campaign> {
  const { data } = await apiClient.post('/campaigns', campaign);
  return data;
}

export async function updateCampaign(id: string, updates: Partial<CampaignCreate>): Promise<Campaign> {
  const { data } = await apiClient.put(`/campaigns/${id}`, updates);
  return data;
}

export async function deleteCampaign(id: string): Promise<void> {
  await apiClient.delete(`/campaigns/${id}`);
}

// Hooks
export function useCampaigns() {
  return useQuery({
    queryKey: campaignKeys.lists(),
    queryFn: fetchCampaigns,
  });
}

export function useCampaign(id: string) {
  return useQuery({
    queryKey: campaignKeys.detail(id),
    queryFn: () => fetchCampaign(id),
    enabled: !!id,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

export function useUpdateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<CampaignCreate> }) =>
      updateCampaign(id, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

export function useDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}
