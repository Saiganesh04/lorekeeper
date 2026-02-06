import { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Play, Plus, Users, Map, BookOpen, Calendar, Clock, Settings } from 'lucide-react';
import { motion } from 'framer-motion';
import { useCampaign } from '../api/campaigns';
import { useSessions, useCreateSession } from '../api/sessions';
import { useCharacters } from '../api/characters';
import { useGameStore } from '../stores/gameStore';
import Card, { CardContent, CardHeader, CardTitle, CardFooter } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { LoadingState } from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';

export default function CampaignPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const navigate = useNavigate();
  const { setCampaign, setPartyMembers } = useGameStore();

  const { data: campaign, isLoading: campaignLoading } = useCampaign(campaignId!);
  const { data: sessionsData, isLoading: sessionsLoading } = useSessions(campaignId!);
  const { data: charactersData } = useCharacters(campaignId!, { type: 'pc' });
  const createSession = useCreateSession();

  // Update game store when campaign loads
  useEffect(() => {
    if (campaign) {
      setCampaign(campaign);
    }
  }, [campaign, setCampaign]);

  useEffect(() => {
    if (charactersData?.characters) {
      setPartyMembers(charactersData.characters);
    }
  }, [charactersData, setPartyMembers]);

  const handleStartSession = async () => {
    try {
      const session = await createSession.mutateAsync({ campaignId: campaignId! });
      navigate(`/sessions/${session.id}`);
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleContinueSession = (sessionId: string) => {
    navigate(`/sessions/${sessionId}`);
  };

  if (campaignLoading || sessionsLoading) {
    return <LoadingState message="Loading campaign..." />;
  }

  if (!campaign) {
    return (
      <div className="p-8 text-center">
        <p className="text-danger">Campaign not found</p>
        <Link to="/" className="text-primary hover:underline mt-4 inline-block">
          Back to home
        </Link>
      </div>
    );
  }

  const sessions = sessionsData?.sessions || [];
  const activeSession = sessions.find((s) => s.status === 'active');
  const partyMembers = charactersData?.characters || [];

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Campaign Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-heading text-primary">{campaign.name}</h1>
              <Badge variant="primary">{campaign.genre}</Badge>
              <Badge variant="secondary">{campaign.tone}</Badge>
            </div>
            <p className="text-text-muted max-w-2xl">{campaign.description || 'No description'}</p>
          </div>
          <Button variant="ghost" size="sm" leftIcon={<Settings className="w-4 h-4" />}>
            Settings
          </Button>
        </div>

        {/* Quick Stats */}
        <div className="flex items-center gap-6 text-sm text-text-muted">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            <span>{campaign.session_count} sessions</span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            <span>{campaign.character_count} characters</span>
          </div>
          <div className="flex items-center gap-2">
            <Map className="w-4 h-4" />
            <span>{campaign.location_count} locations</span>
          </div>
        </div>
      </motion.div>

      {/* Main Action */}
      <Card variant="highlighted" className="mb-8">
        <CardContent className="py-8 text-center">
          {activeSession ? (
            <>
              <h2 className="text-xl font-heading text-primary mb-2">Continue Your Adventure</h2>
              <p className="text-text-muted mb-4">
                Session {activeSession.session_number} is in progress
              </p>
              <Button
                size="lg"
                onClick={() => handleContinueSession(activeSession.id)}
                leftIcon={<Play className="w-5 h-5" />}
              >
                Continue Session
              </Button>
            </>
          ) : (
            <>
              <h2 className="text-xl font-heading text-primary mb-2">Ready to Play?</h2>
              <p className="text-text-muted mb-4">Start a new session and let the story unfold</p>
              <Button
                size="lg"
                onClick={handleStartSession}
                isLoading={createSession.isPending}
                leftIcon={<Plus className="w-5 h-5" />}
              >
                Start New Session
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Party Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Party</CardTitle>
              <Link
                to={`/campaigns/${campaignId}/characters`}
                className="text-sm text-primary hover:underline"
              >
                Manage
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {partyMembers.length === 0 ? (
              <EmptyState
                icon={<Users className="w-8 h-8" />}
                title="No party members"
                description="Add characters to start your adventure"
                action={{
                  label: 'Add Characters',
                  onClick: () => navigate(`/campaigns/${campaignId}/characters`),
                }}
              />
            ) : (
              <div className="space-y-3">
                {partyMembers.slice(0, 4).map((char) => (
                  <div
                    key={char.id}
                    className="flex items-center justify-between p-2 bg-background-tertiary rounded"
                  >
                    <div>
                      <span className="font-heading text-primary">{char.name}</span>
                      <span className="text-text-muted text-sm ml-2">
                        {char.race} {char.char_class}
                      </span>
                    </div>
                    <span className="text-sm text-text-muted">Lv. {char.level}</span>
                  </div>
                ))}
                {partyMembers.length > 4 && (
                  <p className="text-sm text-text-muted text-center">
                    +{partyMembers.length - 4} more
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sessions History */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            {sessions.length === 0 ? (
              <p className="text-text-muted text-center py-4">No sessions yet</p>
            ) : (
              <div className="space-y-3">
                {sessions.slice(0, 5).map((session) => (
                  <div
                    key={session.id}
                    className="flex items-center justify-between p-2 bg-background-tertiary rounded cursor-pointer hover:bg-background-tertiary/70"
                    onClick={() => handleContinueSession(session.id)}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-heading text-primary">
                        Session {session.session_number}
                      </span>
                      {session.status === 'active' && (
                        <Badge variant="success" size="sm">
                          Active
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-1 text-sm text-text-muted">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(session.started_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Links */}
        <Card>
          <CardHeader>
            <CardTitle>Explore</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link
              to={`/campaigns/${campaignId}/world`}
              className="flex items-center gap-3 p-3 bg-background-tertiary rounded hover:bg-background-tertiary/70 transition-colors"
            >
              <Map className="w-5 h-5 text-accent" />
              <div>
                <span className="font-heading text-primary block">World Map</span>
                <span className="text-sm text-text-muted">Explore locations</span>
              </div>
            </Link>
            <Link
              to={`/campaigns/${campaignId}/knowledge`}
              className="flex items-center gap-3 p-3 bg-background-tertiary rounded hover:bg-background-tertiary/70 transition-colors"
            >
              <BookOpen className="w-5 h-5 text-accent" />
              <div>
                <span className="font-heading text-primary block">Knowledge Graph</span>
                <span className="text-sm text-text-muted">View connections</span>
              </div>
            </Link>
            <Link
              to={`/campaigns/${campaignId}/characters`}
              className="flex items-center gap-3 p-3 bg-background-tertiary rounded hover:bg-background-tertiary/70 transition-colors"
            >
              <Users className="w-5 h-5 text-accent" />
              <div>
                <span className="font-heading text-primary block">Characters</span>
                <span className="text-sm text-text-muted">Manage party & NPCs</span>
              </div>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
