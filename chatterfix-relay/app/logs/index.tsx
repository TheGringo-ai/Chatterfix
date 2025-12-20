/**
 * Voice Logs Screen
 * Shows all voice command logs with sync status
 */

import { View, Text, FlatList, Pressable } from 'react-native';

// Placeholder data - will be replaced with WatermelonDB query
const PLACEHOLDER_LOGS = [
  {
    id: '1',
    transcript: 'Create work order for pump failure',
    commandType: 'work_order',
    createdAt: new Date(),
    isSynced: true,
  },
  {
    id: '2',
    transcript: 'Check out bearing kit from inventory',
    commandType: 'checkout',
    createdAt: new Date(Date.now() - 3600000),
    isSynced: false,
  },
  {
    id: '3',
    transcript: 'Inspect conveyor belt tension',
    commandType: 'inspection',
    createdAt: new Date(Date.now() - 7200000),
    isSynced: true,
  },
];

export default function LogsScreen() {
  const getCommandIcon = (type: string) => {
    switch (type) {
      case 'work_order': return '📋';
      case 'checkout': return '📦';
      case 'inspection': return '🔍';
      case 'query': return '❓';
      default: return '🎤';
    }
  };

  return (
    <View className="flex-1 bg-background">
      <FlatList
        data={PLACEHOLDER_LOGS}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16 }}
        renderItem={({ item }) => (
          <Pressable className="bg-background-card rounded-xl p-4 mb-3">
            <View className="flex-row items-start">
              {/* Command type icon */}
              <Text className="text-2xl mr-3">{getCommandIcon(item.commandType)}</Text>

              {/* Log content */}
              <View className="flex-1">
                <Text className="text-white font-medium">{item.transcript}</Text>
                <View className="flex-row items-center mt-2">
                  <Text className="text-gray-400 text-sm">
                    {item.createdAt.toLocaleTimeString()}
                  </Text>
                  <View className="mx-2 w-1 h-1 bg-gray-500 rounded-full" />
                  <Text className={`text-sm ${item.isSynced ? 'text-success' : 'text-warning'}`}>
                    {item.isSynced ? '✓ Synced' : '⏳ Pending'}
                  </Text>
                </View>
              </View>
            </View>
          </Pressable>
        )}
        ListEmptyComponent={
          <View className="items-center py-8">
            <Text className="text-gray-400 text-lg">No voice logs yet</Text>
            <Text className="text-gray-500">Record a voice command to get started</Text>
          </View>
        }
      />
    </View>
  );
}
