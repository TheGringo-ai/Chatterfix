/**
 * Dashboard Screen - Shows KPIs and summary metrics
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';

interface KPIData {
  mttr: { value: number; unit: string; status: string };
  mtbf: { value: number; unit: string; status: string };
  asset_utilization: { average_utilization: number; status: string };
  cost_tracking: { total_cost: number };
  work_order_metrics: { completion_rate: number; total_created: number };
}

export default function DashboardScreen() {
  const {
    data: kpiData,
    isLoading,
    refetch,
    isRefetching,
  } = useQuery<KPIData>({
    queryKey: ['kpi-summary'],
    queryFn: () => apiService.getKPISummary(30),
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent':
      case 'good':
        return '#27ae60';
      case 'warning':
        return '#f39c12';
      case 'critical':
        return '#e74c3c';
      default:
        return '#3498db';
    }
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={isRefetching}
          onRefresh={refetch}
          tintColor="#3498db"
        />
      }
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>📊 Dashboard</Text>
        <Text style={styles.headerSubtitle}>Real-time KPIs</Text>
      </View>

      {isLoading ? (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading KPIs...</Text>
        </View>
      ) : (
        <View style={styles.kpiGrid}>
          {/* MTTR Card */}
          <View style={styles.kpiCard}>
            <Text style={styles.kpiIcon}>⏱️</Text>
            <Text style={styles.kpiValue}>
              {kpiData?.mttr?.value || 0} hrs
            </Text>
            <Text style={styles.kpiLabel}>MTTR</Text>
            <View
              style={[
                styles.statusBadge,
                { backgroundColor: getStatusColor(kpiData?.mttr?.status || '') },
              ]}
            >
              <Text style={styles.statusText}>
                {kpiData?.mttr?.status || 'N/A'}
              </Text>
            </View>
          </View>

          {/* MTBF Card */}
          <View style={styles.kpiCard}>
            <Text style={styles.kpiIcon}>🔄</Text>
            <Text style={styles.kpiValue}>
              {kpiData?.mtbf?.value || 0} hrs
            </Text>
            <Text style={styles.kpiLabel}>MTBF</Text>
            <View
              style={[
                styles.statusBadge,
                { backgroundColor: getStatusColor(kpiData?.mtbf?.status || '') },
              ]}
            >
              <Text style={styles.statusText}>
                {kpiData?.mtbf?.status || 'N/A'}
              </Text>
            </View>
          </View>

          {/* Utilization Card */}
          <View style={styles.kpiCard}>
            <Text style={styles.kpiIcon}>📈</Text>
            <Text style={styles.kpiValue}>
              {kpiData?.asset_utilization?.average_utilization || 0}%
            </Text>
            <Text style={styles.kpiLabel}>Utilization</Text>
            <View
              style={[
                styles.statusBadge,
                {
                  backgroundColor: getStatusColor(
                    kpiData?.asset_utilization?.status || ''
                  ),
                },
              ]}
            >
              <Text style={styles.statusText}>
                {kpiData?.asset_utilization?.status || 'N/A'}
              </Text>
            </View>
          </View>

          {/* Cost Card */}
          <View style={styles.kpiCard}>
            <Text style={styles.kpiIcon}>💰</Text>
            <Text style={styles.kpiValue}>
              ${(kpiData?.cost_tracking?.total_cost || 0).toLocaleString()}
            </Text>
            <Text style={styles.kpiLabel}>Total Cost</Text>
          </View>

          {/* Completion Rate Card */}
          <View style={[styles.kpiCard, styles.wideCard]}>
            <Text style={styles.kpiIcon}>✅</Text>
            <Text style={styles.kpiValue}>
              {kpiData?.work_order_metrics?.completion_rate || 0}%
            </Text>
            <Text style={styles.kpiLabel}>
              Completion Rate ({kpiData?.work_order_metrics?.total_created || 0}{' '}
              Work Orders)
            </Text>
          </View>
        </View>
      )}

      {/* Quick Actions */}
      <View style={styles.quickActions}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionButtons}>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>➕</Text>
            <Text style={styles.actionText}>New Work Order</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>📷</Text>
            <Text style={styles.actionText}>Scan Asset</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>🎤</Text>
            <Text style={styles.actionText}>Voice Command</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  header: {
    padding: 20,
    backgroundColor: '#1e3c72',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginTop: 4,
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
  },
  loadingText: {
    color: '#fff',
    fontSize: 16,
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
    justifyContent: 'space-between',
  },
  kpiCard: {
    width: '48%',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 15,
    padding: 15,
    marginBottom: 10,
    alignItems: 'center',
  },
  wideCard: {
    width: '100%',
  },
  kpiIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  kpiValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  kpiLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 4,
    textAlign: 'center',
  },
  statusBadge: {
    marginTop: 8,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  quickActions: {
    padding: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 15,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flex: 1,
    backgroundColor: 'rgba(52, 152, 219, 0.2)',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
    marginHorizontal: 5,
    borderWidth: 1,
    borderColor: 'rgba(52, 152, 219, 0.3)',
  },
  actionIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  actionText: {
    color: '#3498db',
    fontSize: 12,
    fontWeight: '500',
    textAlign: 'center',
  },
});
