import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Plus, Users, UserCircle, Heart, Shield, Swords } from 'lucide-react';
import { motion } from 'framer-motion';
import { useCharacters, useCreateCharacter, useCreateNPC } from '../api/characters';
import Card, { CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import { LoadingState } from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import type { Character } from '../types';

export default function CharactersPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const [activeTab, setActiveTab] = useState<'pc' | 'npc'>('pc');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { data: pcsData, isLoading: pcsLoading } = useCharacters(campaignId!, { type: 'pc' });
  const { data: npcsData, isLoading: npcsLoading } = useCharacters(campaignId!, { type: 'npc' });
  const createCharacter = useCreateCharacter();
  const createNPC = useCreateNPC();

  const [newCharacter, setNewCharacter] = useState({
    name: '',
    race: '',
    char_class: '',
    level: 1,
    hp_max: 10,
  });

  const [newNPC, setNewNPC] = useState({
    name: '',
    role: '',
    generateWithAI: true,
  });

  const handleCreateCharacter = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createCharacter.mutateAsync({
        campaignId: campaignId!,
        character: {
          ...newCharacter,
          character_type: 'pc',
        },
      });
      setIsCreateModalOpen(false);
      setNewCharacter({ name: '', race: '', char_class: '', level: 1, hp_max: 10 });
    } catch (err) {
      console.error('Failed to create character:', err);
    }
  };

  const handleCreateNPC = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createNPC.mutateAsync({
        campaignId: campaignId!,
        options: {
          name: newNPC.name || undefined,
          role: newNPC.role || undefined,
          generateWithAI: newNPC.generateWithAI,
        },
      });
      setIsCreateModalOpen(false);
      setNewNPC({ name: '', role: '', generateWithAI: true });
    } catch (err) {
      console.error('Failed to create NPC:', err);
    }
  };

  if (pcsLoading || npcsLoading) {
    return <LoadingState message="Loading characters..." />;
  }

  const pcs = pcsData?.characters || [];
  const npcs = npcsData?.characters || [];
  const characters = activeTab === 'pc' ? pcs : npcs;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-heading text-primary">Characters</h1>
        <Button onClick={() => setIsCreateModalOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
          {activeTab === 'pc' ? 'Add Character' : 'Create NPC'}
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab('pc')}
          className={`px-4 py-2 rounded-lg font-heading transition-colors ${
            activeTab === 'pc'
              ? 'bg-primary text-background'
              : 'bg-background-secondary text-text-muted hover:text-text'
          }`}
        >
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            <span>Party ({pcs.length})</span>
          </div>
        </button>
        <button
          onClick={() => setActiveTab('npc')}
          className={`px-4 py-2 rounded-lg font-heading transition-colors ${
            activeTab === 'npc'
              ? 'bg-primary text-background'
              : 'bg-background-secondary text-text-muted hover:text-text'
          }`}
        >
          <div className="flex items-center gap-2">
            <UserCircle className="w-4 h-4" />
            <span>NPCs ({npcs.length})</span>
          </div>
        </button>
      </div>

      {/* Character Grid */}
      {characters.length === 0 ? (
        <EmptyState
          icon={activeTab === 'pc' ? <Users className="w-16 h-16" /> : <UserCircle className="w-16 h-16" />}
          title={activeTab === 'pc' ? 'No party members yet' : 'No NPCs yet'}
          description={
            activeTab === 'pc'
              ? 'Create player characters to build your adventuring party'
              : 'NPCs will appear as you explore the world or create them manually'
          }
          action={{
            label: activeTab === 'pc' ? 'Create Character' : 'Create NPC',
            onClick: () => setIsCreateModalOpen(true),
          }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {characters.map((char, index) => (
            <motion.div
              key={char.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <CharacterCard character={char} />
            </motion.div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title={activeTab === 'pc' ? 'Create Character' : 'Create NPC'}
        size="lg"
      >
        {activeTab === 'pc' ? (
          <form onSubmit={handleCreateCharacter} className="space-y-4">
            <div>
              <label className="block text-sm font-heading text-primary mb-2">Name</label>
              <input
                type="text"
                value={newCharacter.name}
                onChange={(e) => setNewCharacter({ ...newCharacter, name: e.target.value })}
                placeholder="Character name"
                className="input-fantasy"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-heading text-primary mb-2">Race</label>
                <input
                  type="text"
                  value={newCharacter.race}
                  onChange={(e) => setNewCharacter({ ...newCharacter, race: e.target.value })}
                  placeholder="Human, Elf, Dwarf..."
                  className="input-fantasy"
                />
              </div>
              <div>
                <label className="block text-sm font-heading text-primary mb-2">Class</label>
                <input
                  type="text"
                  value={newCharacter.char_class}
                  onChange={(e) => setNewCharacter({ ...newCharacter, char_class: e.target.value })}
                  placeholder="Fighter, Wizard..."
                  className="input-fantasy"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-heading text-primary mb-2">Level</label>
                <input
                  type="number"
                  value={newCharacter.level}
                  onChange={(e) => setNewCharacter({ ...newCharacter, level: parseInt(e.target.value) || 1 })}
                  min={1}
                  max={20}
                  className="input-fantasy"
                />
              </div>
              <div>
                <label className="block text-sm font-heading text-primary mb-2">Max HP</label>
                <input
                  type="number"
                  value={newCharacter.hp_max}
                  onChange={(e) => setNewCharacter({ ...newCharacter, hp_max: parseInt(e.target.value) || 10 })}
                  min={1}
                  className="input-fantasy"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" isLoading={createCharacter.isPending}>
                Create
              </Button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleCreateNPC} className="space-y-4">
            <div>
              <label className="block text-sm font-heading text-primary mb-2">Name (optional)</label>
              <input
                type="text"
                value={newNPC.name}
                onChange={(e) => setNewNPC({ ...newNPC, name: e.target.value })}
                placeholder="Leave blank to generate"
                className="input-fantasy"
              />
            </div>
            <div>
              <label className="block text-sm font-heading text-primary mb-2">Role</label>
              <input
                type="text"
                value={newNPC.role}
                onChange={(e) => setNewNPC({ ...newNPC, role: e.target.value })}
                placeholder="Innkeeper, Guard, Merchant..."
                className="input-fantasy"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="generateWithAI"
                checked={newNPC.generateWithAI}
                onChange={(e) => setNewNPC({ ...newNPC, generateWithAI: e.target.checked })}
                className="w-4 h-4 accent-primary"
              />
              <label htmlFor="generateWithAI" className="text-text">
                Generate personality with AI
              </label>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" isLoading={createNPC.isPending}>
                Create NPC
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}

// Character Card Component
function CharacterCard({ character }: { character: Character }) {
  const hpPercentage = (character.hp_current / character.hp_max) * 100;

  return (
    <Card hoverable>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>{character.name}</CardTitle>
            <p className="text-sm text-text-muted">
              {character.race} {character.char_class}
            </p>
          </div>
          <Badge variant="primary">Lv. {character.level}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* HP Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <div className="flex items-center gap-1 text-danger">
              <Heart className="w-4 h-4" />
              <span>HP</span>
            </div>
            <span className="font-mono text-text-muted">
              {character.hp_current}/{character.hp_max}
            </span>
          </div>
          <div className="h-2 bg-background rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-danger to-red-400 transition-all"
              style={{ width: `${hpPercentage}%` }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-2 bg-background-tertiary rounded">
            <Shield className="w-4 h-4 mx-auto text-accent mb-1" />
            <span className="text-xs text-text-muted">AC</span>
            <span className="block font-mono text-primary">{character.armor_class}</span>
          </div>
          <div className="p-2 bg-background-tertiary rounded">
            <Swords className="w-4 h-4 mx-auto text-secondary mb-1" />
            <span className="text-xs text-text-muted">STR</span>
            <span className="block font-mono text-primary">
              {character.strength_modifier >= 0 ? '+' : ''}
              {character.strength_modifier}
            </span>
          </div>
          <div className="p-2 bg-background-tertiary rounded">
            <span className="text-xs text-text-muted">DEX</span>
            <span className="block font-mono text-primary">
              {character.dexterity_modifier >= 0 ? '+' : ''}
              {character.dexterity_modifier}
            </span>
          </div>
        </div>

        {/* Personality traits for NPCs */}
        {character.character_type === 'npc' && character.personality_traits && (
          <div className="mt-4">
            <span className="text-xs text-text-muted">Personality:</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {character.personality_traits.slice(0, 3).map((trait, i) => (
                <Badge key={i} variant="secondary" size="sm">
                  {trait}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
