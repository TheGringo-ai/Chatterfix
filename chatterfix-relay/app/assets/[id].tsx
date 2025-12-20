/**
 * Asset Detail Screen
 * Shows asset details and related voice logs
 */

import { View, Text, ScrollView } from 'react-native';
import { useLocalSearchParams } from 'expo-router';

export default function AssetDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  // Placeholder - will be replaced with WatermelonDB query
  const asset = {
    id,
    name: 'Hydraulic Press #1',
    status: 'operational',
    assetTag: 'HP-001',
    location: 'Building A, Bay 3',
  };

  return (
    <ScrollView className="flex-1 bg-background">
      <View className="p-4">
        {/* Asset Card */}
        <View className="bg-background-card rounded-xl p-4 mb-4">
          <View className="flex-row items-center mb-3">
            <View className="w-4 h-4 rounded-full bg-success mr-3" />
            <Text className="text-white text-2xl font-bold">{asset.name}</Text>
          </View>

          <View className="space-y-2">
            <View className="flex-row">
              <Text className="text-gray-400 w-24">Asset Tag:</Text>
              <Text className="text-white">{asset.assetTag}</Text>
            </View>
            <View className="flex-row">
              <Text className="text-gray-400 w-24">Location:</Text>
              <Text className="text-white">{asset.location}</Text>
            </View>
            <View className="flex-row">
              <Text className="text-gray-400 w-24">Status:</Text>
              <Text className="text-success capitalize">{asset.status}</Text>
            </View>
          </View>
        </View>

        {/* Recent Logs */}
        <Text className="text-white text-xl font-bold mb-3">Recent Voice Logs</Text>
        <View className="bg-background-card rounded-xl p-4">
          <Text className="text-gray-400 text-center py-4">
            No voice logs for this asset yet
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}
