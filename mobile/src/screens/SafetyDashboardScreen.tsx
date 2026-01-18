/**
 * SafetyDashboardScreen - Safety Management Hub
 *
 * Central hub for all safety features in ChatterFix:
 * - Quick incident/observation reporting
 * - Safety metrics overview
 * - Access to inspections, training, and SafetyFred AI coach
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

interface SafetyMetrics {
  days_since_last_incident: number;
  open_incidents: number;
  near_misses_this_month: number;
  inspections_due: number;
  safety_score: number;
  observations_this_month: number;
}

interface QuickAction {
  id: string;
  label: string;
  icon: string;
  color: string;
  screen?: string;
  action?: () => void;
}

export default function SafetyDashboardScreen() {
  const navigation = useNavigation<any>();
  const { user, isAuthenticated } = useAuth();
  const [metrics, setMetrics] = useState<SafetyMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const quickActions: QuickAction[] = [
    {
      id: 'incident',
      label: 'Report Incident',
      icon: '🚨',
      color: '#e74c3c',
      screen: 'IncidentReport',
    },
    {
      id: 'observation',
      label: 'Safety Observation',
      icon: '👁️',
      color: '#f39c12',
      screen: 'SafetyObservation',
    },
    {
      id: 'inspection',
      label: 'Start Inspection',
      icon: '📋',
      color: '#3498db',
      screen: 'SafetyInspection',
    },
    {
      id: 'safety_fred',
      label: 'Ask SafetyFred',
      icon: '🦺',
      color: '#27ae60',
      screen: 'SafetyChat',
    },
  ];

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);

      // In demo mode or when not authenticated, use demo data
      if (!isAuthenticated) {
        setMetrics({
          days_since_last_incident: 45,
          open_incidents: 2,
          near_misses_this_month: 8,
          inspections_due: 3,
          safety_score: 94.5,
          observations_this_month: 23,
        });
        return;
      }

      // Fetch real data from API
      const response = await api.get('/api/v1/safety/dashboard');
      if (response.data?.summary) {
        setMetrics({
          days_since_last_incident: response.data.summary.days_since_last_incident || 0,
          open_incidents: response.data.summary.open_incidents || 0,
          near_misses_this_month: response.data.summary.near_misses || 0,
          inspections_due: 3, // Demo
          safety_score: response.data.summary.safety_score || 0,
          observations_this_month: response.data.summary.total_observations || 0,
        });
      }
    } catch (error) {
      console.error('Failed to load safety dashboard:', error);
      // Use demo data on error
      setMetrics({
        days_since_last_incident: 45,
        open_incidents: 2,
        near_misses_this_month: 8,
        inspections_due: 3,
        safety_score: 94.5,
        observations_this_month: 23,
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadDashboard();
  };

  const handleQuickAction = (action: QuickAction) => {
    if (action.screen) {
      navigation.navigate(action.screen);
    } else if (action.action) {
      action.action();
    }
  };

  const getSafetyScoreColor = (score: number) => {
    if (score >= 90) return '#27ae60';
    if (score >= 70) return '#f39c12';
    return '#e74c3c';
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3498db" />
          <Text style={styles.loadingText}>Loading Safety Dashboard...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#fff" />
        }
      >
        {/* Safety Score Banner */}
        <View style={[styles.scoreBanner, { backgroundColor: getSafetyScoreColor(metrics?.safety_score || 0) }]}>
          <Text style={styles.scoreLabel}>Safety Score</Text>
          <Text style={styles.scoreValue}>{metrics?.safety_score?.toFixed(1) || '0'}%</Text>
          <Text style={styles.scoreDays}>
            {metrics?.days_since_last_incident || 0} days since last recordable incident
          </Text>
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.quickActionsGrid}>
            {quickActions.map((action) => (
              <TouchableOpacity
                key={action.id}
                style={[styles.quickActionCard, { borderColor: action.color }]}
                onPress={() => handleQuickAction(action)}
              >
                <Text style={styles.quickActionIcon}>{action.icon}</Text>
                <Text style={styles.quickActionLabel}>{action.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Metrics Cards */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>This Month</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>{metrics?.open_incidents || 0}</Text>
              <Text style={styles.metricLabel}>Open Incidents</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>{metrics?.near_misses_this_month || 0}</Text>
              <Text style={styles.metricLabel}>Near Misses</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>{metrics?.observations_this_month || 0}</Text>
              <Text style={styles.metricLabel}>Observations</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>{metrics?.inspections_due || 0}</Text>
              <Text style={styles.metricLabel}>Inspections Due</Text>
            </View>
          </View>
        </View>

        {/* Voice Report Button */}
        <TouchableOpacity
          style={styles.voiceReportButton}
          onPress={() => navigation.navigate('Voice', { mode: 'safety' })}
        >
          <Text style={styles.voiceReportIcon}>🎤</Text>
          <View style={styles.voiceReportText}>
            <Text style={styles.voiceReportTitle}>Voice Report</Text>
            <Text style={styles.voiceReportSubtitle}>
              Say "Report incident" or "Near miss" to quickly log safety events
            </Text>
          </View>
        </TouchableOpacity>

        {/* Safety Tips */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Safety Tip of the Day</Text>
          <View style={styles.tipCard}>
            <Text style={styles.tipIcon}>💡</Text>
            <Text style={styles.tipText}>
              Always inspect PPE before use. Damaged equipment doesn't protect - report and replace immediately.
            </Text>
          </View>
        </View>

        {/* Recent Activity */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Activity</Text>
          <View style={styles.activityList}>
            <View style={styles.activityItem}>
              <Text style={styles.activityIcon}>✅</Text>
              <View style={styles.activityContent}>
                <Text style={styles.activityTitle}>Daily Walkthrough Completed</Text>
                <Text style={styles.activityTime}>2 hours ago - Production Floor</Text>
              </View>
            </View>
            <View style={styles.activityItem}>
              <Text style={styles.activityIcon}>👁️</Text>
              <View style={styles.activityContent}>
                <Text style={styles.activityTitle}>Safety Observation Submitted</Text>
                <Text style={styles.activityTime}>4 hours ago - Warehouse</Text>
              </View>
            </View>
            <View style={styles.activityItem}>
              <Text style={styles.activityIcon}>🔧</Text>
              <View style={styles.activityContent}>
                <Text style={styles.activityTitle}>Corrective Action Closed</Text>
                <Text style={styles.activityTime}>Yesterday - INC-2024-00042</Text>
              </View>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#a0a0a0',
    marginTop: 10,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  scoreBanner: {
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 20,
  },
  scoreLabel: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 14,
    fontWeight: '600',
  },
  scoreValue: {
    color: '#fff',
    fontSize: 48,
    fontWeight: 'bold',
  },
  scoreDays: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 14,
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickActionCard: {
    width: '48%',
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
    borderWidth: 2,
  },
  quickActionIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  quickActionLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    width: '48%',
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  metricValue: {
    color: '#3498db',
    fontSize: 32,
    fontWeight: 'bold',
  },
  metricLabel: {
    color: '#a0a0a0',
    fontSize: 12,
    marginTop: 4,
  },
  voiceReportButton: {
    backgroundColor: '#1e3c72',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  voiceReportIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  voiceReportText: {
    flex: 1,
  },
  voiceReportTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  voiceReportSubtitle: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 12,
    marginTop: 2,
  },
  tipCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  tipIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  tipText: {
    color: '#fff',
    fontSize: 14,
    flex: 1,
    lineHeight: 20,
  },
  activityList: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    overflow: 'hidden',
  },
  activityItem: {
    flexDirection: 'row',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2d2d4a',
  },
  activityIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  activityContent: {
    flex: 1,
  },
  activityTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  activityTime: {
    color: '#a0a0a0',
    fontSize: 12,
    marginTop: 2,
  },
});
