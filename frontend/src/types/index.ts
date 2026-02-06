// Campaign Types
export interface Campaign {
  id: string;
  name: string;
  description: string | null;
  genre: 'fantasy' | 'sci-fi' | 'horror' | 'steampunk';
  tone: 'serious' | 'lighthearted' | 'dark' | 'epic';
  setting_description: string | null;
  world_rules: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  session_count: number;
  character_count: number;
  location_count: number;
}

export interface CampaignCreate {
  name: string;
  description?: string;
  genre?: 'fantasy' | 'sci-fi' | 'horror' | 'steampunk';
  tone?: 'serious' | 'lighthearted' | 'dark' | 'epic';
  setting_description?: string;
}

// Session Types
export interface GameSession {
  id: string;
  campaign_id: string;
  session_number: number;
  status: 'active' | 'completed' | 'paused';
  recap: string | null;
  notes: string | null;
  started_at: string;
  ended_at: string | null;
  event_count: number;
  encounter_count: number;
}

// Character Types
export interface Character {
  id: string;
  campaign_id: string;
  name: string;
  character_type: 'pc' | 'npc' | 'monster';
  race: string | null;
  char_class: string | null;
  level: number;
  hp_current: number;
  hp_max: number;
  armor_class: number;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  personality_traits: string[] | null;
  backstory: string | null;
  appearance: string | null;
  motivation: string | null;
  secret: string | null;
  speech_pattern: string | null;
  disposition: number;
  inventory: Record<string, unknown>[] | null;
  equipment: Record<string, unknown> | null;
  gold: number;
  experience_points: number;
  skills: Record<string, number> | null;
  proficiencies: string[] | null;
  languages: string[] | null;
  is_alive: boolean;
  conditions: string[] | null;
  current_location_id: string | null;
  created_at: string;
  updated_at: string;
  strength_modifier: number;
  dexterity_modifier: number;
  constitution_modifier: number;
  intelligence_modifier: number;
  wisdom_modifier: number;
  charisma_modifier: number;
}

export interface CharacterCreate {
  name: string;
  character_type?: 'pc' | 'npc' | 'monster';
  race?: string;
  char_class?: string;
  level?: number;
  hp_max?: number;
  armor_class?: number;
  strength?: number;
  dexterity?: number;
  constitution?: number;
  intelligence?: number;
  wisdom?: number;
  charisma?: number;
  personality_traits?: string[];
  backstory?: string;
  appearance?: string;
}

// Story Event Types
export type Mood = 'tense' | 'calm' | 'mysterious' | 'triumphant' | 'somber' | 'humorous' | 'urgent' | 'peaceful' | 'neutral';

export interface DiceRollResult {
  notation: string;
  total: number;
  rolls: number[];
  modifier: number;
  success: boolean | null;
  critical: 'hit' | 'fail' | null;
}

export interface NewEntity {
  name: string;
  entity_type: string;
  description: string;
}

export interface KnowledgeUpdate {
  action: string;
  entity: string;
  relationship?: string;
  target?: string;
}

export interface StoryEvent {
  id: string;
  session_id: string;
  event_type: 'narrative' | 'dialogue' | 'combat' | 'roll' | 'system' | 'choice';
  content: string;
  player_action: string | null;
  choices: string[] | null;
  mood: Mood;
  speaker: string | null;
  dice_rolls: DiceRollResult[] | null;
  new_entities: NewEntity[] | null;
  knowledge_updates: KnowledgeUpdate[] | null;
  xp_awarded: number | null;
  items_awarded: Record<string, unknown>[] | null;
  sequence_order: number;
  created_at: string;
}

export interface StoryFeed {
  session_id: string;
  events: StoryEvent[];
  total_events: number;
  current_mood: Mood;
  current_location: string | null;
}

// Encounter Types
export interface EnemyStats {
  id: string;
  name: string;
  hp_current: number;
  hp_max: number;
  armor_class: number;
  speed: number;
  abilities?: Record<string, number>;
  attacks?: { name: string; damage: string; to_hit: string }[];
  special_abilities?: { name: string; description: string }[];
  is_defeated: boolean;
}

export interface InitiativeEntry {
  character_id: string;
  character_name: string;
  initiative_roll: number;
  is_enemy: boolean;
  is_current: boolean;
}

export interface Encounter {
  id: string;
  session_id: string;
  location_id: string | null;
  name: string;
  encounter_type: 'combat' | 'social' | 'puzzle' | 'exploration' | 'boss';
  description: string;
  difficulty: 'easy' | 'medium' | 'hard' | 'deadly';
  status: 'active' | 'resolved' | 'fled' | 'failed';
  current_round: number;
  current_phase: string | null;
  enemies: EnemyStats[] | null;
  initiative_order: InitiativeEntry[] | null;
  current_turn_index: number;
  combat_log: Record<string, unknown>[] | null;
  environmental_effects: string[] | null;
  terrain_features: string[] | null;
  rewards: { xp: number; gold: number; items: string[] } | null;
  created_at: string;
  ended_at: string | null;
}

// Location Types
export interface Location {
  id: string;
  campaign_id: string;
  name: string;
  location_type: string;
  description: string | null;
  detailed_description: string | null;
  x_coord: number;
  y_coord: number;
  danger_level: number;
  is_discovered: boolean;
  terrain: string | null;
  climate: string | null;
  atmosphere: string | null;
  points_of_interest: { name: string; description: string }[] | null;
  environmental_effects: string[] | null;
  connected_locations: { location_id: string; name: string; path_type: string; travel_time?: string }[] | null;
  parent_location_id: string | null;
}

// Knowledge Graph Types
export interface KnowledgeNode {
  id: string;
  campaign_id: string;
  node_type: 'character' | 'location' | 'event' | 'item' | 'faction' | 'quest' | 'lore';
  name: string;
  description: string | null;
  entity_id: string | null;
  entity_type: string | null;
  properties: Record<string, unknown> | null;
  importance: number;
  first_mentioned_at: string;
  last_updated_at: string;
  connection_count: number;
}

export interface KnowledgeEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: string;
  properties: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
}

export interface KnowledgeGraph {
  campaign_id: string;
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
  node_count: number;
  edge_count: number;
}

// Map Types
export interface MapNode {
  id: string;
  name: string;
  type: string;
  x: number;
  y: number;
  danger_level: number;
  is_discovered: boolean;
  terrain: string | null;
  parent_id: string | null;
}

export interface MapEdge {
  source: string;
  target: string;
  path_type: string;
  travel_time: string | null;
}

export interface MapData {
  campaign_id: string;
  nodes: MapNode[];
  edges: MapEdge[];
  total_locations: number;
}

// Dice Types
export interface DiceRollRequest {
  notation: string;
  advantage?: boolean;
  disadvantage?: boolean;
}

export interface DiceRollResponse {
  notation: string;
  total: number;
  rolls: number[];
  modifier: number;
  success: boolean | null;
  critical: 'hit' | 'fail' | null;
  advantage_rolls: number[] | null;
}

// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}
