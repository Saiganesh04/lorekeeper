import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { StoryEvent, StoryFeed } from '../types';

// Query keys
export const narrativeKeys = {
  all: ['narrative'] as const,
  stories: () => [...narrativeKeys.all, 'story'] as const,
  story: (sessionId: string) => [...narrativeKeys.stories(), sessionId] as const,
  events: () => [...narrativeKeys.all, 'event'] as const,
  event: (id: string) => [...narrativeKeys.events(), id] as const,
};

// API functions
export async function fetchStoryFeed(sessionId: string, skip = 0, limit = 50): Promise<StoryFeed> {
  const { data } = await apiClient.get(`/sessions/${sessionId}/story`, {
    params: { skip, limit },
  });
  return data;
}

export async function submitPlayerAction(sessionId: string, action: string, context?: string): Promise<StoryEvent> {
  const { data } = await apiClient.post(`/sessions/${sessionId}/action`, {
    action,
    context,
  });
  return data;
}

export async function generateOpening(sessionId: string, style = 'dramatic', includeRecap = false): Promise<StoryEvent> {
  const { data } = await apiClient.post(`/sessions/${sessionId}/opening`, {
    style,
    include_recap: includeRecap,
  });
  return data;
}

export async function selectChoice(sessionId: string, eventId: string, choiceIndex: number): Promise<StoryEvent> {
  const { data } = await apiClient.post(`/sessions/${sessionId}/choice`, {
    event_id: eventId,
    choice_index: choiceIndex,
  });
  return data;
}

export async function generateRecap(sessionId: string): Promise<{
  session_id: string;
  session_number: number;
  recap: string;
  key_events: string[];
  characters_met: string[];
  locations_visited: string[];
  items_acquired: string[];
  total_xp: number;
}> {
  const { data } = await apiClient.post(`/sessions/${sessionId}/recap`);
  return data;
}

// Hooks
export function useStoryFeed(sessionId: string) {
  return useQuery({
    queryKey: narrativeKeys.story(sessionId),
    queryFn: () => fetchStoryFeed(sessionId),
    enabled: !!sessionId,
    refetchInterval: false, // Don't auto-refetch, we'll update manually
  });
}

export function useSubmitAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sessionId, action, context }: { sessionId: string; action: string; context?: string }) =>
      submitPlayerAction(sessionId, action, context),
    onSuccess: (data) => {
      // Add the new event to the story feed
      queryClient.setQueryData<StoryFeed>(narrativeKeys.story(data.session_id), (old) => {
        if (!old) return old;
        return {
          ...old,
          events: [...old.events, data],
          total_events: old.total_events + 1,
          current_mood: data.mood,
        };
      });
    },
  });
}

export function useGenerateOpening() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sessionId, style, includeRecap }: { sessionId: string; style?: string; includeRecap?: boolean }) =>
      generateOpening(sessionId, style, includeRecap),
    onSuccess: (data) => {
      queryClient.setQueryData<StoryFeed>(narrativeKeys.story(data.session_id), (old) => {
        if (!old) {
          return {
            session_id: data.session_id,
            events: [data],
            total_events: 1,
            current_mood: data.mood,
            current_location: null,
          };
        }
        return {
          ...old,
          events: [...old.events, data],
          total_events: old.total_events + 1,
          current_mood: data.mood,
        };
      });
    },
  });
}

export function useSelectChoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sessionId, eventId, choiceIndex }: { sessionId: string; eventId: string; choiceIndex: number }) =>
      selectChoice(sessionId, eventId, choiceIndex),
    onSuccess: (data) => {
      queryClient.setQueryData<StoryFeed>(narrativeKeys.story(data.session_id), (old) => {
        if (!old) return old;
        return {
          ...old,
          events: [...old.events, data],
          total_events: old.total_events + 1,
          current_mood: data.mood,
        };
      });
    },
  });
}

export function useGenerateRecap() {
  return useMutation({
    mutationFn: (sessionId: string) => generateRecap(sessionId),
  });
}
