/**
 * Offline Indicator Component
 * Shows when the app is offline
 */

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { apiService } from '../services/api';

export default function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const checkOnlineStatus = () => {
      setIsOnline(apiService.getOnlineStatus());
    };

    // Check immediately
    checkOnlineStatus();

    // Check every 5 seconds
    const interval = setInterval(checkOnlineStatus, 5000);

    return () => clearInterval(interval);
  }, []);

  if (isOnline) {
    return null;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.text}>📡 Offline - Using cached data</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#e74c3c',
    paddingHorizontal: 15,
    paddingVertical: 8,
    alignItems: 'center',
  },
  text: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
});