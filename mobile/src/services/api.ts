/**
 * API Service for ChatterFix Mobile App
 * Handles all API communication with the backend
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { AxiosError, AxiosInstance } from 'axios';

// Configure base URL
// In production, this should be set via environment variables or app configuration
// For Expo: Use Constants.expoConfig?.extra?.apiBaseUrl
// For React Native CLI: Use react-native-config
const getApiBaseUrl = (): string => {
  // Check for environment-based configuration first
  // @ts-ignore - This would be set by react-native-config or similar
  if (typeof process !== 'undefined' && process.env?.REACT_NATIVE_API_BASE_URL) {
    // @ts-ignore
    return process.env.REACT_NATIVE_API_BASE_URL;
  }

  // Default fallback - update this for your deployment
  return 'https://chatterfix.com'; // Production URL
};

const API_BASE_URL = getApiBaseUrl();

// Storage keys
const STORAGE_KEYS = {
  AUTH_TOKEN: 'authToken', // Changed to match Firebase token storage
  USER_DATA: '@chatterfix_user_data',
  OFFLINE_QUEUE: '@chatterfix_offline_queue',
  CACHED_DATA: '@chatterfix_cached_data',
};

class ApiService {
  private client: AxiosInstance;
  private isOnline: boolean = true;
  private retryQueue: Array<{ resolve: Function; reject: Function; config: any }> = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 15000, // Increased timeout for mobile
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.setupNetworkMonitoring();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (!error.response) {
          // Network error - switch to offline mode
          this.isOnline = false;
          console.log('Network error - switching to offline mode');

          // Queue the request for retry when back online
          return new Promise((resolve, reject) => {
            this.retryQueue.push({ resolve, reject, config: error.config });
          });
        }

        // Handle 401 unauthorized (token expired)
        if (error.response?.status === 401) {
          await AsyncStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
          // Could trigger re-authentication here
        }

        return Promise.reject(error);
      }
    );
  }

  private setupNetworkMonitoring() {
    // Simple network monitoring - in production, use NetInfo from @react-native-community/netinfo
    const checkOnlineStatus = async () => {
      try {
        await this.client.get('/health', { timeout: 5000 });
        if (!this.isOnline) {
          this.isOnline = true;
          this.processRetryQueue();
        }
      } catch {
        this.isOnline = false;
      }
    };

    // Check every 30 seconds
    setInterval(checkOnlineStatus, 30000);
  }

  private async processRetryQueue() {
    while (this.retryQueue.length > 0) {
      const { resolve, reject, config } = this.retryQueue.shift()!;
      try {
        const response = await this.client.request(config);
        resolve(response);
      } catch (error) {
        reject(error);
      }
    }
  }

  // Set online status
  setOnlineStatus(isOnline: boolean) {
    this.isOnline = isOnline;
  }

  // Get online status
  getOnlineStatus(): boolean {
    return this.isOnline;
  }

  // Force retry queued requests
  async retryQueuedRequests() {
    if (this.isOnline) {
      await this.processRetryQueue();
    }
  }

  // ========== Authentication ==========

  // Note: Authentication is now handled by Firebase
  // These methods are kept for backward compatibility but use Firebase tokens

  async setAuthToken(token: string): Promise<void> {
    await AsyncStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
  }

  async logout(): Promise<void> {
    await AsyncStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    await AsyncStorage.removeItem(STORAGE_KEYS.USER_DATA);
  }

  async getStoredToken(): Promise<string | null> {
    return await AsyncStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
  }

  // ========== KPI & Analytics ==========

  async getKPISummary(days: number = 30): Promise<any> {
    try {
      const response = await this.client.get(`/analytics/kpi/summary?days=${days}`);
      // Cache the response
      await this.cacheData('kpi_summary', response.data);
      return response.data;
    } catch (error) {
      // Return cached data if offline
      return this.getCachedData('kpi_summary');
    }
  }

  async getTrendData(metric: string, days: number = 30): Promise<any> {
    try {
      const response = await this.client.get(`/analytics/trends/${metric}?days=${days}`);
      return response.data;
    } catch (error) {
      return this.getCachedData(`trend_${metric}`);
    }
  }

  // ========== Work Orders ==========

  async getWorkOrders(status?: string): Promise<any[]> {
    try {
      const params = status ? `?status=${status}` : '';
      const response = await this.client.get(`/work-orders${params}`);
      await this.cacheData('work_orders', response.data);
      return response.data;
    } catch (error) {
      return this.getCachedData('work_orders') || [];
    }
  }

  async getWorkOrder(id: number): Promise<any> {
    try {
      const response = await this.client.get(`/work-orders/${id}`);
      return response.data;
    } catch (error) {
      const cached = await this.getCachedData('work_orders');
      return cached?.find((wo: any) => wo.id === id);
    }
  }

  async createWorkOrder(workOrder: any): Promise<any> {
    if (!this.isOnline) {
      // Queue for later sync
      await this.queueOfflineAction('create_work_order', workOrder);
      return { ...workOrder, id: Date.now(), offline: true };
    }

    const response = await this.client.post('/work-orders', workOrder);
    return response.data;
  }

  async updateWorkOrder(id: number, data: any): Promise<any> {
    if (!this.isOnline) {
      await this.queueOfflineAction('update_work_order', { id, ...data });
      return { id, ...data, offline: true };
    }

    const response = await this.client.put(`/work-orders/${id}`, data);
    return response.data;
  }

  // ========== Assets ==========

  async getAssets(): Promise<any[]> {
    try {
      const response = await this.client.get('/assets/');
      await this.cacheData('assets', response.data);
      return response.data;
    } catch (error) {
      return this.getCachedData('assets') || [];
    }
  }

  async getAsset(id: number): Promise<any> {
    try {
      const response = await this.client.get(`/assets/${id}`);
      return response.data;
    } catch (error) {
      const cached = await this.getCachedData('assets');
      return cached?.find((asset: any) => asset.id === id);
    }
  }

  async getAssetSensorData(assetId: number): Promise<any> {
    try {
      const response = await this.client.get(`/iot/sensors/asset/${assetId}/summary`);
      return response.data;
    } catch (error) {
      return null;
    }
  }

  // ========== IoT Sensors ==========

  async recordSensorReading(reading: any): Promise<any> {
    if (!this.isOnline) {
      await this.queueOfflineAction('sensor_reading', reading);
      return { ...reading, offline: true };
    }

    const response = await this.client.post('/iot/sensors/data', reading);
    return response.data;
  }

  async getSensorAlerts(hours: number = 24): Promise<any[]> {
    try {
      const response = await this.client.get(`/iot/sensors/alerts?hours=${hours}`);
      return response.data;
    } catch (error) {
      return [];
    }
  }

  // ========== AI Assistant ==========

  async sendMessage(message: string, context?: string): Promise<any> {
    const response = await this.client.post('/ai/chat', { message, context });
    return response.data;
  }

  // ========== Push Notifications ==========

  async registerPushToken(token: string, userId: number): Promise<any> {
    const response = await this.client.post('/api/push/register', {
      user_id: userId,
      subscription: { endpoint: token },
    });
    return response.data;
  }

  // ========== Offline Support ==========

  private async cacheData(key: string, data: any): Promise<void> {
    try {
      const cached = await AsyncStorage.getItem(STORAGE_KEYS.CACHED_DATA);
      const cacheObj = cached ? JSON.parse(cached) : {};
      cacheObj[key] = {
        data,
        timestamp: Date.now(),
      };
      await AsyncStorage.setItem(STORAGE_KEYS.CACHED_DATA, JSON.stringify(cacheObj));
    } catch (error) {
      console.error('Error caching data:', error);
    }
  }

  private async getCachedData(key: string): Promise<any> {
    try {
      const cached = await AsyncStorage.getItem(STORAGE_KEYS.CACHED_DATA);
      if (cached) {
        const cacheObj = JSON.parse(cached);
        return cacheObj[key]?.data;
      }
    } catch (error) {
      console.error('Error reading cached data:', error);
    }
    return null;
  }

  private async queueOfflineAction(type: string, data: any): Promise<void> {
    try {
      const queue = await AsyncStorage.getItem(STORAGE_KEYS.OFFLINE_QUEUE);
      const queueArr = queue ? JSON.parse(queue) : [];
      queueArr.push({
        type,
        data,
        timestamp: Date.now(),
      });
      await AsyncStorage.setItem(STORAGE_KEYS.OFFLINE_QUEUE, JSON.stringify(queueArr));
    } catch (error) {
      console.error('Error queuing offline action:', error);
    }
  }

  async syncOfflineData(): Promise<{ success: number; failed: number }> {
    const results = { success: 0, failed: 0 };

    try {
      const queue = await AsyncStorage.getItem(STORAGE_KEYS.OFFLINE_QUEUE);
      if (!queue) return results;

      const queueArr = JSON.parse(queue);
      const remaining = [];

      for (const item of queueArr) {
        try {
          switch (item.type) {
            case 'create_work_order':
              await this.client.post('/work-orders', item.data);
              break;
            case 'update_work_order':
              const { id, ...updateData } = item.data;
              await this.client.put(`/work-orders/${id}`, updateData);
              break;
            case 'sensor_reading':
              await this.client.post('/iot/sensors/data', item.data);
              break;
            default:
              console.log('Unknown action type:', item.type);
          }
          results.success++;
        } catch (error) {
          remaining.push(item);
          results.failed++;
        }
      }

      await AsyncStorage.setItem(
        STORAGE_KEYS.OFFLINE_QUEUE,
        JSON.stringify(remaining)
      );
    } catch (error) {
      console.error('Error syncing offline data:', error);
    }

    return results;
  }

  async getOfflineQueueCount(): Promise<number> {
    try {
      const queue = await AsyncStorage.getItem(STORAGE_KEYS.OFFLINE_QUEUE);
      return queue ? JSON.parse(queue).length : 0;
    } catch (error) {
      return 0;
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();
