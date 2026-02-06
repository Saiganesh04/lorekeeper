import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, BookOpen, Calendar, Users, MapPin, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { useCampaigns, useCreateCampaign } from '../api/campaigns';
import Card, { CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import { LoadingState } from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';

export default function HomePage() {
  const { data, isLoading, error } = useCampaigns();
  const createCampaign = useCreateCampaign();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newCampaign, setNewCampaign] = useState({
    name: '',
    description: '',
    genre: 'fantasy' as const,
    tone: 'serious' as const,
  });

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createCampaign.mutateAsync(newCampaign);
      setIsCreateModalOpen(false);
      setNewCampaign({ name: '', description: '', genre: 'fantasy', tone: 'serious' });
    } catch (err) {
      console.error('Failed to create campaign:', err);
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading campaigns..." />;
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-danger">Failed to load campaigns</p>
      </div>
    );
  }

  const campaigns = data?.campaigns || [];

  return (
    <div className="min-h-full p-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-center gap-3 mb-4"
        >
          <Sparkles className="w-8 h-8 text-primary" />
          <h1 className="text-4xl font-heading text-primary">Welcome to Lorekeeper</h1>
          <Sparkles className="w-8 h-8 text-primary" />
        </motion.div>
        <p className="text-text-muted text-lg max-w-2xl mx-auto">
          Your AI-powered Dungeon Master for epic tabletop adventures. Create worlds, forge
          legends, and let the story unfold.
        </p>
      </div>

      {/* Campaigns Section */}
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-heading text-primary">Your Campaigns</h2>
          <Button onClick={() => setIsCreateModalOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
            New Campaign
          </Button>
        </div>

        {campaigns.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="w-16 h-16" />}
            title="No campaigns yet"
            description="Start your first adventure by creating a new campaign. Choose your genre, set the tone, and let the AI help weave your story."
            action={{
              label: 'Create Your First Campaign',
              onClick: () => setIsCreateModalOpen(true),
            }}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {campaigns.map((campaign, index) => (
              <motion.div
                key={campaign.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Link to={`/campaigns/${campaign.id}`}>
                  <Card hoverable className="h-full">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <CardTitle>{campaign.name}</CardTitle>
                        <Badge variant="primary" size="sm">
                          {campaign.genre}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-text-muted mb-4 line-clamp-2">
                        {campaign.description || 'No description'}
                      </p>
                      <div className="flex items-center gap-4 text-sm text-text-muted">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          <span>{campaign.session_count} sessions</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          <span>{campaign.character_count} characters</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          <span>{campaign.location_count} locations</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Create Campaign Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Campaign"
        size="lg"
      >
        <form onSubmit={handleCreateCampaign} className="space-y-6">
          <div>
            <label className="block text-sm font-heading text-primary mb-2">Campaign Name</label>
            <input
              type="text"
              value={newCampaign.name}
              onChange={(e) => setNewCampaign({ ...newCampaign, name: e.target.value })}
              placeholder="The Chronicles of..."
              className="input-fantasy"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-heading text-primary mb-2">Description</label>
            <textarea
              value={newCampaign.description}
              onChange={(e) => setNewCampaign({ ...newCampaign, description: e.target.value })}
              placeholder="A tale of adventure and mystery..."
              className="input-fantasy min-h-[100px]"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-heading text-primary mb-2">Genre</label>
              <select
                value={newCampaign.genre}
                onChange={(e) =>
                  setNewCampaign({ ...newCampaign, genre: e.target.value as typeof newCampaign.genre })
                }
                className="input-fantasy"
              >
                <option value="fantasy">Fantasy</option>
                <option value="sci-fi">Sci-Fi</option>
                <option value="horror">Horror</option>
                <option value="steampunk">Steampunk</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-heading text-primary mb-2">Tone</label>
              <select
                value={newCampaign.tone}
                onChange={(e) =>
                  setNewCampaign({ ...newCampaign, tone: e.target.value as typeof newCampaign.tone })
                }
                className="input-fantasy"
              >
                <option value="serious">Serious</option>
                <option value="lighthearted">Lighthearted</option>
                <option value="dark">Dark</option>
                <option value="epic">Epic</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createCampaign.isPending}>
              Create Campaign
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
