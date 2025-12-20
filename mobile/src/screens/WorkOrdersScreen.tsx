/**
 * Work Orders Screen - List and manage work orders
 *
 * Supports two modes:
 * - Standard Mode: Full details, dark theme (office/manager)
 * - Field Mode: Simplified cards, high contrast (outdoor/technician)
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
  Alert,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { useFieldMode } from '../contexts/FieldModeContext';

interface WorkOrder {
  id: number;
  title: string;
  description: string;
  status: string;
  priority: string;
  asset_id: number;
  due_date: string;
  assigned_to: string;
}

export default function WorkOrdersScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<string | null>(null);
  const { isFieldMode, theme } = useFieldMode();

  const {
    data: workOrders,
    isLoading,
    refetch,
    isRefetching,
  } = useQuery<WorkOrder[]>({
    queryKey: ['work-orders'],
    queryFn: () => apiService.getWorkOrders(),
  });

  // Handle starting a work order (Field Mode action)
  const handleStartWorkOrder = (workOrder: WorkOrder) => {
    Alert.alert(
      'Start Work Order',
      `Begin work on: ${workOrder.title}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'START',
          style: 'default',
          onPress: () => {
            // TODO: Update work order status to "In Progress"
            Alert.alert('Started', `Work order ${workOrder.id} is now in progress.`);
          },
        },
      ]
    );
  };

  const getPriorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'urgent':
      case 'high':
        return '#e74c3c';
      case 'medium':
        return '#f39c12';
      case 'low':
        return '#27ae60';
      default:
        return '#3498db';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return '#27ae60';
      case 'in progress':
        return '#3498db';
      case 'open':
        return '#f39c12';
      case 'on hold':
        return '#e74c3c';
      default:
        return '#7f8c8d';
    }
  };

  const filteredWorkOrders = workOrders?.filter((wo) => {
    const matchesSearch =
      wo.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      wo.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = !filter || wo.status === filter;
    return matchesSearch && matchesFilter;
  });

  // Field Mode: Simplified card with BIG START button
  const renderFieldModeCard = ({ item }: { item: WorkOrder }) => (
    <View style={[styles.fieldCard, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
      {/* Priority indicator strip */}
      <View style={[styles.fieldPriorityStrip, { backgroundColor: getPriorityColor(item.priority) }]} />

      <View style={styles.fieldCardContent}>
        {/* Asset/Title - Big and readable */}
        <Text style={[styles.fieldTitle, { color: theme.textPrimary }]} numberOfLines={1}>
          {item.title}
        </Text>

        {/* Problem summary */}
        <Text style={[styles.fieldDescription, { color: theme.textSecondary }]} numberOfLines={2}>
          {item.description || 'No description'}
        </Text>

        {/* BIG GREEN START BUTTON */}
        {item.status?.toLowerCase() !== 'completed' && (
          <TouchableOpacity
            style={styles.startButton}
            onPress={() => handleStartWorkOrder(item)}
            activeOpacity={0.7}
          >
            <Text style={styles.startButtonText}>START</Text>
          </TouchableOpacity>
        )}

        {/* Completed indicator */}
        {item.status?.toLowerCase() === 'completed' && (
          <View style={styles.completedBadge}>
            <Text style={styles.completedText}>DONE</Text>
          </View>
        )}
      </View>
    </View>
  );

  // Standard Mode: Full details card
  const renderStandardCard = ({ item }: { item: WorkOrder }) => (
    <TouchableOpacity style={styles.workOrderCard}>
      <View style={styles.cardHeader}>
        <View
          style={[
            styles.priorityBadge,
            { backgroundColor: getPriorityColor(item.priority) },
          ]}
        >
          <Text style={styles.priorityText}>{item.priority}</Text>
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
      <Text style={styles.workOrderTitle}>{item.title}</Text>
      <Text style={styles.workOrderDescription} numberOfLines={2}>
        {item.description}
      </Text>
      <View style={styles.cardFooter}>
        <Text style={styles.footerText}>📅 {item.due_date || 'No due date'}</Text>
        <Text style={styles.footerText}>👤 {item.assigned_to || 'Unassigned'}</Text>
      </View>
    </TouchableOpacity>
  );

  const renderWorkOrder = isFieldMode ? renderFieldModeCard : renderStandardCard;

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Field Mode Indicator */}
      {isFieldMode && (
        <View style={styles.fieldModeIndicator}>
          <Text style={styles.fieldModeText}>FIELD MODE</Text>
        </View>
      )}

      {/* Search Bar - Hidden in Field Mode for simplicity */}
      {!isFieldMode && (
        <View style={styles.searchContainer}>
          <TextInput
            style={styles.searchInput}
            placeholder="Search work orders..."
            placeholderTextColor="#7f8c8d"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>
      )}

      {/* Filter Buttons */}
      <View style={styles.filterContainer}>
        {['All', 'Open', 'In Progress', 'Completed'].map((filterOption) => (
          <TouchableOpacity
            key={filterOption}
            style={[
              styles.filterButton,
              (filter === filterOption || (filterOption === 'All' && !filter)) &&
                styles.filterButtonActive,
            ]}
            onPress={() =>
              setFilter(filterOption === 'All' ? null : filterOption)
            }
          >
            <Text
              style={[
                styles.filterText,
                (filter === filterOption || (filterOption === 'All' && !filter)) &&
                  styles.filterTextActive,
              ]}
            >
              {filterOption}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Work Orders List */}
      {isLoading ? (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading work orders...</Text>
        </View>
      ) : (
        <FlatList
          data={filteredWorkOrders}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderWorkOrder}
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
              <Text style={styles.emptyText}>No work orders found</Text>
            </View>
          }
        />
      )}

      {/* FAB for creating new work order */}
      <TouchableOpacity style={styles.fab}>
        <Text style={styles.fabText}>+</Text>
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
  filterContainer: {
    flexDirection: 'row',
    paddingHorizontal: 15,
    marginBottom: 10,
  },
  filterButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  filterButtonActive: {
    backgroundColor: '#3498db',
    borderColor: '#3498db',
  },
  filterText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 13,
  },
  filterTextActive: {
    color: '#fff',
    fontWeight: '600',
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
    paddingBottom: 80,
  },
  workOrderCard: {
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
    marginBottom: 10,
  },
  priorityBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  priorityText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
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
  workOrderTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 6,
  },
  workOrderDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: 10,
    lineHeight: 20,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
    paddingTop: 10,
  },
  footerText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
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
    bottom: 20,
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
    fontSize: 32,
    color: '#fff',
    fontWeight: '300',
  },
  // Field Mode Styles
  fieldModeIndicator: {
    backgroundColor: '#ff6600',
    paddingVertical: 8,
    alignItems: 'center',
  },
  fieldModeText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
    letterSpacing: 2,
  },
  fieldCard: {
    flexDirection: 'row',
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 2,
    overflow: 'hidden',
    minHeight: 120,
  },
  fieldPriorityStrip: {
    width: 8,
  },
  fieldCardContent: {
    flex: 1,
    padding: 16,
    justifyContent: 'space-between',
  },
  fieldTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
  },
  fieldDescription: {
    fontSize: 16,
    lineHeight: 22,
    marginBottom: 12,
  },
  startButton: {
    backgroundColor: '#00aa00',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 56,
  },
  startButtonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: 2,
  },
  completedBadge: {
    backgroundColor: '#666666',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 56,
  },
  completedText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 2,
  },
});
