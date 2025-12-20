/**
 * Assets List Screen
 * Shows all tracked assets with sync status
 */

import { View, Text, FlatList, Pressable, ActivityIndicator } from 'react-native';
import { Link } from 'expo-router';
import { useAssets } from '@/hooks';

export default function AssetsScreen() {
  const { assets, loading, error, refresh, addAsset } = useAssets();

  // Demo: Add sample assets if none exist
  const seedDemoData = async () => {
    const demoAssets = [
      { name: 'Hydraulic Press #1', status: 'operational' as const, location: 'Building A' },
      { name: 'CNC Mill Station 3', status: 'warning' as const, location: 'Machine Shop' },
      { name: 'Conveyor Belt A', status: 'critical' as const, location: 'Warehouse' },
    ];
    for (const asset of demoAssets) {
      await addAsset(asset);
    }
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'bg-success';
      case 'warning': return 'bg-warning';
      case 'critical': return 'bg-danger';
      default: return 'bg-gray-500';
    }
  };

  if (loading) {
    return (
      <View className="flex-1 bg-background items-center justify-center">
        <ActivityIndicator size="large" color="#00d4ff" />
      </View>
    );
  }

  if (error) {
    return (
      <View className="flex-1 bg-background items-center justify-center p-4">
        <Text className="text-danger text-lg">{error}</Text>
        <Pressable onPress={refresh} className="mt-4 bg-primary px-4 py-2 rounded">
          <Text className="text-background font-bold">Retry</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View className="flex-1 bg-background">
      <FlatList
        data={assets}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16 }}
        renderItem={({ item }) => (
          <Link href={`/assets/${item.id}`} asChild>
            <Pressable className="bg-background-card rounded-xl p-4 mb-3 flex-row items-center">
              {/* Status indicator */}
              <View className={`w-3 h-3 rounded-full ${getStatusColor(item.status)} mr-3`} />

              {/* Asset info */}
              <View className="flex-1">
                <Text className="text-white font-semibold text-lg">{item.name}</Text>
                <Text className="text-gray-400 capitalize">{item.status}</Text>
              </View>

              {/* Chevron */}
              <Text className="text-gray-500 text-xl">›</Text>
            </Pressable>
          </Link>
        )}
        ListEmptyComponent={
          <View className="items-center py-8">
            <Text className="text-gray-400 text-lg">No assets found</Text>
            <Text className="text-gray-500 mb-4">Add assets to start tracking</Text>
            <Pressable onPress={seedDemoData} className="bg-primary px-6 py-3 rounded-xl">
              <Text className="text-background font-bold">Add Demo Assets</Text>
            </Pressable>
          </View>
        }
        onRefresh={refresh}
        refreshing={loading}
      />
    </View>
  );
}
