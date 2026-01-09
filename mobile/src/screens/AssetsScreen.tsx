/**
 * Assets Screen - View and manage assets
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  TextInput,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';

interface Asset {
  id: number;
  name: string;
  asset_tag: string;
  status: string;
  location: string;
  criticality: string;
  condition_rating: number;
}

export default function AssetsScreen() {
  const [searchQuery, setSearchQuery] = useState('');

  const {
    data: assets,
    isLoading,
    refetch,
    isRefetching,
  } = useQuery<Asset[]>({
    queryKey: ['assets'],
    queryFn: () => apiService.getAssets(),
  });

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return '#27ae60';
      case 'maintenance':
        return '#f39c12';
      case 'inactive':
      case 'down':
        return '#e74c3c';
      default:
        return '#7f8c8d';
    }
  };

  const getCriticalityColor = (criticality: string) => {
    switch (criticality?.toLowerCase()) {
      case 'critical':
        return '#e74c3c';
      case 'high':
        return '#f39c12';
      case 'medium':
        return '#3498db';
      case 'low':
        return '#27ae60';
      default:
        return '#7f8c8d';
    }
  };

  const getConditionEmoji = (rating: number) => {
    if (rating >= 8) return '🟢';
    if (rating >= 6) return '🟡';
    if (rating >= 4) return '🟠';
    return '🔴';
  };

  const filteredAssets = assets?.filter((asset) =>
    asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    asset.asset_tag?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    asset.location?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const renderAsset = ({ item }: { item: Asset }) => (
    <TouchableOpacity style={styles.assetCard}>
      <View style={styles.cardHeader}>
        <View style={styles.assetInfo}>
          <Text style={styles.assetName}>{item.name}</Text>
          <Text style={styles.assetTag}>{item.asset_tag || 'No Tag'}</Text>
        </View>
        <View
          style={[
            styles.statusBadge,
            { backgroundColor: getStatusColor(item.status) },
          ]}
        >
          <Text style={styles.statusText}>{item.status}</Text>
        </View>
      </View>

      <View style={styles.cardDetails}>
        <View style={styles.detailItem}>
          <Text style={styles.detailLabel}>📍 Location</Text>
          <Text style={styles.detailValue}>{item.location || 'Unknown'}</Text>
        </View>
        <View style={styles.detailItem}>
          <Text style={styles.detailLabel}>⚡ Criticality</Text>
          <Text
            style={[
              styles.detailValue,
              { color: getCriticalityColor(item.criticality) },
            ]}
          >
            {item.criticality || 'N/A'}
          </Text>
        </View>
        <View style={styles.detailItem}>
          <Text style={styles.detailLabel}>📊 Condition</Text>
          <Text style={styles.detailValue}>
            {getConditionEmoji(item.condition_rating)} {item.condition_rating}/10
          </Text>
        </View>
      </View>

      <View style={styles.cardActions}>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionText}>📷 Photo</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionText}>📋 Work Order</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionText}>🔍 Details</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search assets..."
          placeholderTextColor="#7f8c8d"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {/* Asset Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{assets?.length || 0}</Text>
          <Text style={styles.statLabel}>Total</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: '#27ae60' }]}>
            {assets?.filter((a) => a.status === 'Active').length || 0}
          </Text>
          <Text style={styles.statLabel}>Active</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: '#f39c12' }]}>
            {assets?.filter((a) => a.status === 'Maintenance').length || 0}
          </Text>
          <Text style={styles.statLabel}>Maintenance</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: '#e74c3c' }]}>
            {assets?.filter((a) => a.criticality === 'Critical').length || 0}
          </Text>
          <Text style={styles.statLabel}>Critical</Text>
        </View>
      </View>

      {/* Assets List */}
      {isLoading ? (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading assets...</Text>
        </View>
      ) : (
        <FlatList
          data={filteredAssets}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderAsset}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor="#3498db"
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No assets found</Text>
            </View>
          }
        />
      )}

      {/* FAB for scanning */}
      <TouchableOpacity style={styles.fab}>
        <Text style={styles.fabText}>📷</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  searchContainer: {
    padding: 15,
  },
  searchInput: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 15,
    color: '#fff',
    fontSize: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 15,
    paddingBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    marginTop: 2,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#fff',
    fontSize: 16,
  },
  listContent: {
    padding: 15,
    paddingBottom: 160, // Extra padding for FAB positioned above tab bar
  },
  assetCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 15,
    padding: 15,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  assetInfo: {
    flex: 1,
  },
  assetName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  assetTag: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
  cardDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  detailItem: {
    alignItems: 'center',
    flex: 1,
  },
  detailLabel: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.5)',
  },
  detailValue: {
    fontSize: 13,
    color: '#fff',
    marginTop: 2,
    fontWeight: '500',
  },
  cardActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    marginHorizontal: 4,
    backgroundColor: 'rgba(52, 152, 219, 0.2)',
    borderRadius: 8,
  },
  actionText: {
    color: '#3498db',
    fontSize: 12,
    fontWeight: '500',
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 16,
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 90, // Positioned above tab bar (tab bar ~60px + padding)
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#3498db',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#3498db',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  fabText: {
    fontSize: 28,
  },
});
