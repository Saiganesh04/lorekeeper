import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Search, Network, Users, MapPin, Calendar, Package, Flag, ScrollText, BookOpen } from 'lucide-react';
import { motion } from 'framer-motion';
import Card, { CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { LoadingState } from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';

const nodeTypeIcons: Record<string, React.ReactNode> = {
  character: <Users className="w-4 h-4" />,
  location: <MapPin className="w-4 h-4" />,
  event: <Calendar className="w-4 h-4" />,
  item: <Package className="w-4 h-4" />,
  faction: <Flag className="w-4 h-4" />,
  quest: <ScrollText className="w-4 h-4" />,
  lore: <BookOpen className="w-4 h-4" />,
};

const nodeTypeColors: Record<string, string> = {
  character: 'text-primary',
  location: 'text-success',
  event: 'text-accent',
  item: 'text-secondary',
  faction: 'text-warning',
  quest: 'text-info',
  lore: 'text-text-muted',
};

export default function KnowledgePage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string | null>(null);

  // In a full implementation, you would fetch knowledge graph data here
  // For now, showing a placeholder with sample data

  const nodeTypes = ['character', 'location', 'event', 'item', 'faction', 'quest', 'lore'];

  // Sample data
  const sampleNodes = [
    { id: '1', type: 'character', name: 'Aldric the Brave', description: 'A valiant knight seeking redemption', connections: 5 },
    { id: '2', type: 'location', name: 'Thornwood Village', description: 'A small farming community', connections: 3 },
    { id: '3', type: 'event', name: 'The Night of Falling Stars', description: 'A celestial event that changed everything', connections: 7 },
    { id: '4', type: 'item', name: 'The Crystal Blade', description: 'An ancient sword of mysterious origin', connections: 2 },
    { id: '5', type: 'faction', name: 'The Silver Order', description: 'Protectors of the realm', connections: 4 },
    { id: '6', type: 'quest', name: 'Find the Missing Merchant', description: 'A merchant has vanished under suspicious circumstances', connections: 3 },
  ];

  const filteredNodes = sampleNodes.filter((node) => {
    const matchesSearch = node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          node.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = !selectedType || node.type === selectedType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-heading text-primary">Knowledge Graph</h1>
      </div>

      {/* Graph Visualization Placeholder */}
      <Card className="mb-6">
        <CardContent className="p-0">
          <div className="h-[400px] bg-background-tertiary rounded-lg flex items-center justify-center">
            <div className="text-center">
              <Network className="w-16 h-16 text-text-muted mx-auto mb-4 opacity-50" />
              <p className="text-text-muted mb-2">Interactive knowledge graph</p>
              <p className="text-sm text-text-dark">
                The graph visualization would render here using D3.js force-directed layout
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search the knowledge base..."
            className="input-fantasy pl-10"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant={selectedType === null ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setSelectedType(null)}
          >
            All
          </Button>
          {nodeTypes.map((type) => (
            <Button
              key={type}
              variant={selectedType === type ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setSelectedType(type)}
              leftIcon={nodeTypeIcons[type]}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {/* Node List */}
      {filteredNodes.length === 0 ? (
        <EmptyState
          icon={<Network className="w-16 h-16" />}
          title="No entries found"
          description="Try adjusting your search or filters"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredNodes.map((node, index) => (
            <motion.div
              key={node.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card hoverable>
                <CardContent>
                  <div className="flex items-start gap-3">
                    <div className={`p-2 bg-background-tertiary rounded ${nodeTypeColors[node.type]}`}>
                      {nodeTypeIcons[node.type]}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="font-heading text-primary">{node.name}</h3>
                        <Badge variant="secondary" size="sm">
                          {node.type}
                        </Badge>
                      </div>
                      <p className="text-text-muted text-sm mb-2">{node.description}</p>
                      <div className="flex items-center gap-1 text-xs text-text-dark">
                        <Network className="w-3 h-3" />
                        <span>{node.connections} connections</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Legend */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Node Types</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {nodeTypes.map((type) => (
              <div key={type} className="flex items-center gap-2">
                <div className={`p-1.5 bg-background-tertiary rounded ${nodeTypeColors[type]}`}>
                  {nodeTypeIcons[type]}
                </div>
                <span className="text-sm text-text-muted capitalize">{type}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
