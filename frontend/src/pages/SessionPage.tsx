import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Send, Loader2, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { useSession } from '../api/sessions';
import { useStoryFeed, useSubmitAction, useGenerateOpening, useSelectChoice } from '../api/narrative';
import { useCampaign } from '../api/campaigns';
import { useCharacters } from '../api/characters';
import { useGameStore } from '../stores/gameStore';
import Card, { CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { LoadingState } from '../components/ui/LoadingSpinner';
import type { StoryEvent, Mood } from '../types';

export default function SessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { setSession, setCampaign, setPartyMembers, setIsGenerating, isGenerating } = useGameStore();

  const { data: session, isLoading: sessionLoading } = useSession(sessionId!);
  const { data: campaign } = useCampaign(session?.campaign_id || '');
  const { data: charactersData } = useCharacters(session?.campaign_id || '', { type: 'pc' });
  const { data: storyFeed, isLoading: storyLoading } = useStoryFeed(sessionId!);

  const submitAction = useSubmitAction();
  const generateOpening = useGenerateOpening();
  const selectChoice = useSelectChoice();

  const [playerInput, setPlayerInput] = useState('');
  const storyEndRef = useRef<HTMLDivElement>(null);

  // Update game store
  useEffect(() => {
    if (session) setSession(session);
    if (campaign) setCampaign(campaign);
    if (charactersData?.characters) setPartyMembers(charactersData.characters);
  }, [session, campaign, charactersData, setSession, setCampaign, setPartyMembers]);

  // Scroll to bottom when new events appear
  useEffect(() => {
    storyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [storyFeed?.events?.length]);

  // Generate opening if no events
  useEffect(() => {
    if (storyFeed && storyFeed.events.length === 0 && session?.status === 'active' && !isGenerating) {
      setIsGenerating(true);
      generateOpening.mutate(
        { sessionId: sessionId!, style: 'dramatic' },
        {
          onSettled: () => setIsGenerating(false),
        }
      );
    }
  }, [storyFeed, session, sessionId, generateOpening, isGenerating, setIsGenerating]);

  const handleSubmitAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!playerInput.trim() || isGenerating) return;

    setIsGenerating(true);
    try {
      await submitAction.mutateAsync({
        sessionId: sessionId!,
        action: playerInput,
      });
      setPlayerInput('');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectChoice = async (eventId: string, choiceIndex: number) => {
    if (isGenerating) return;

    setIsGenerating(true);
    try {
      await selectChoice.mutateAsync({
        sessionId: sessionId!,
        eventId,
        choiceIndex,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  if (sessionLoading || storyLoading) {
    return <LoadingState message="Loading session..." />;
  }

  if (!session) {
    return (
      <div className="p-8 text-center">
        <p className="text-danger">Session not found</p>
      </div>
    );
  }

  const events = storyFeed?.events || [];
  const lastEvent = events[events.length - 1];
  const hasUnselectedChoices = lastEvent?.choices && lastEvent.choices.length > 0;

  return (
    <div className="h-full flex flex-col">
      {/* Story Feed */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-4">
          <AnimatePresence>
            {events.map((event, index) => (
              <StoryEventCard
                key={event.id}
                event={event}
                isLatest={index === events.length - 1}
                onSelectChoice={handleSelectChoice}
                isGenerating={isGenerating}
              />
            ))}
          </AnimatePresence>

          {/* Generating indicator */}
          {isGenerating && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3 p-4 bg-background-secondary rounded-lg border border-primary/20"
            >
              <Loader2 className="w-5 h-5 text-primary animate-spin" />
              <span className="text-text-muted">The story unfolds...</span>
            </motion.div>
          )}

          <div ref={storyEndRef} />
        </div>
      </div>

      {/* Player Input */}
      <div className="border-t border-primary/20 bg-background-secondary p-4">
        <form onSubmit={handleSubmitAction} className="max-w-4xl mx-auto">
          {/* Suggested actions from last event */}
          {hasUnselectedChoices && !isGenerating && (
            <div className="flex flex-wrap gap-2 mb-3">
              {lastEvent.choices!.map((choice, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleSelectChoice(lastEvent.id, index)}
                  className="px-3 py-1.5 text-sm bg-background-tertiary border border-primary/30 rounded-full text-text hover:border-primary hover:text-primary transition-colors"
                >
                  {choice}
                </button>
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <input
              type="text"
              value={playerInput}
              onChange={(e) => setPlayerInput(e.target.value)}
              placeholder="What do you do?"
              className="flex-1 input-fantasy"
              disabled={isGenerating}
            />
            <Button
              type="submit"
              disabled={!playerInput.trim() || isGenerating}
              isLoading={isGenerating}
              leftIcon={<Send className="w-4 h-4" />}
            >
              Send
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Story Event Card Component
interface StoryEventCardProps {
  event: StoryEvent;
  isLatest: boolean;
  onSelectChoice: (eventId: string, choiceIndex: number) => void;
  isGenerating: boolean;
}

function StoryEventCard({ event, isLatest, onSelectChoice, isGenerating }: StoryEventCardProps) {
  const moodColors: Record<Mood, string> = {
    tense: 'border-l-mood-tense',
    calm: 'border-l-mood-calm',
    mysterious: 'border-l-mood-mysterious',
    triumphant: 'border-l-mood-triumphant',
    somber: 'border-l-mood-somber',
    humorous: 'border-l-mood-humorous',
    urgent: 'border-l-mood-urgent',
    peaceful: 'border-l-mood-peaceful',
    neutral: 'border-l-text-muted',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className={`border-l-4 ${moodColors[event.mood]}`}>
        <CardContent className="py-4">
          {/* Player action */}
          {event.player_action && (
            <div className="mb-3 text-sm">
              <span className="text-primary font-heading">You: </span>
              <span className="text-text-muted italic">"{event.player_action}"</span>
            </div>
          )}

          {/* Narrative content */}
          <div className="prose-fantasy">
            <ReactMarkdown>{event.content}</ReactMarkdown>
          </div>

          {/* Dice rolls */}
          {event.dice_rolls && event.dice_rolls.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {event.dice_rolls.map((roll, index) => (
                <Badge
                  key={index}
                  variant={roll.success ? 'success' : roll.success === false ? 'danger' : 'default'}
                >
                  {roll.notation}: {roll.total}
                  {roll.critical && ` (${roll.critical === 'hit' ? 'CRIT!' : 'FUMBLE!'})`}
                </Badge>
              ))}
            </div>
          )}

          {/* XP awarded */}
          {event.xp_awarded && (
            <div className="mt-3 flex items-center gap-2 text-sm">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-primary">+{event.xp_awarded} XP</span>
            </div>
          )}

          {/* Choices (only show on latest event if not yet selected) */}
          {isLatest && event.choices && event.choices.length > 0 && !isGenerating && (
            <div className="mt-4 pt-4 border-t border-primary/10">
              <p className="text-sm text-text-muted mb-2">What will you do?</p>
              <div className="flex flex-wrap gap-2">
                {event.choices.map((choice, index) => (
                  <Button
                    key={index}
                    variant="secondary"
                    size="sm"
                    onClick={() => onSelectChoice(event.id, index)}
                  >
                    {choice}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
