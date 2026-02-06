import { useParams } from 'react-router-dom';
import { Map, MapPin, Plus, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import Card, { CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { LoadingState } from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';

export default function WorldPage() {
  const { campaignId } = useParams<{ campaignId: string }>();

  // In a full implementation, you would fetch map data here
  // For now, showing a placeholder

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-heading text-primary">World Map</h1>
        <Button leftIcon={<Plus className="w-4 h-4" />}>Add Location</Button>
      </div>

      {/* Map Visualization Placeholder */}
      <Card className="mb-6">
        <CardContent className="p-0">
          <div className="h-[500px] bg-background-tertiary rounded-lg flex items-center justify-center">
            <div className="text-center">
              <Map className="w-16 h-16 text-text-muted mx-auto mb-4 opacity-50" />
              <p className="text-text-muted mb-2">Interactive world map</p>
              <p className="text-sm text-text-dark">
                The map visualization would render here using D3.js or a similar library
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Location List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Sample locations */}
        <LocationCard
          name="The Silver Tankard Inn"
          type="tavern"
          dangerLevel={1}
          isDiscovered={true}
          description="A cozy establishment known for its warm hearth and friendly patrons."
        />
        <LocationCard
          name="Darkwood Forest"
          type="wilderness"
          dangerLevel={5}
          isDiscovered={true}
          description="Ancient trees hide untold secrets and dangers within their shadows."
        />
        <LocationCard
          name="The Sunken Temple"
          type="dungeon"
          dangerLevel={8}
          isDiscovered={false}
          description="???"
        />
      </div>
    </div>
  );
}

interface LocationCardProps {
  name: string;
  type: string;
  dangerLevel: number;
  isDiscovered: boolean;
  description: string;
}

function LocationCard({ name, type, dangerLevel, isDiscovered, description }: LocationCardProps) {
  const dangerColors = {
    low: 'text-success',
    medium: 'text-warning',
    high: 'text-danger',
  };

  const dangerCategory = dangerLevel <= 3 ? 'low' : dangerLevel <= 6 ? 'medium' : 'high';

  return (
    <Card hoverable className={!isDiscovered ? 'opacity-60' : ''}>
      <CardContent>
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-primary" />
            <h3 className="font-heading text-primary">
              {isDiscovered ? name : '???'}
            </h3>
          </div>
          {isDiscovered && (
            <Badge variant="secondary" size="sm">
              {type}
            </Badge>
          )}
        </div>

        <p className="text-text-muted text-sm mb-3">
          {isDiscovered ? description : 'Location not yet discovered'}
        </p>

        {isDiscovered && (
          <div className="flex items-center gap-1 text-sm">
            <AlertTriangle className={`w-4 h-4 ${dangerColors[dangerCategory]}`} />
            <span className={dangerColors[dangerCategory]}>
              Danger Level: {dangerLevel}/10
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
