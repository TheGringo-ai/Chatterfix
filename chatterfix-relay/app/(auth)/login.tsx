import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { Link, router } from 'expo-router';
import { authService } from '@/services/authService';
import { useAppStore } from '@/stores/appStore';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const setOrganizationId = useAppStore((state) => state.setOrganizationId);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter both email and password.');
      return;
    }

    setLoading(true);
    try {
      const userData = await authService.signIn(email, password);
      if (userData.organizationId) {
        setOrganizationId(userData.organizationId);
      }
      router.replace('/');
    } catch (error: any) {
      Alert.alert('Login Failed', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-gray-900"
    >
      <View className="flex-1 justify-center px-8">
        {/* Logo/Title */}
        <View className="items-center mb-12">
          <Text className="text-4xl font-bold text-cyan-400">ChatterFix</Text>
          <Text className="text-lg text-gray-400 mt-2">Relay</Text>
        </View>

        {/* Login Form */}
        <View className="space-y-4">
          <View>
            <Text className="text-gray-400 mb-2">Email</Text>
            <TextInput
              className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700"
              placeholder="Enter your email"
              placeholderTextColor="#6B7280"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
          </View>

          <View>
            <Text className="text-gray-400 mb-2">Password</Text>
            <TextInput
              className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700"
              placeholder="Enter your password"
              placeholderTextColor="#6B7280"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              autoComplete="password"
            />
          </View>

          <TouchableOpacity
            className={`bg-cyan-500 py-4 rounded-lg mt-4 ${
              loading ? 'opacity-50' : ''
            }`}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text className="text-white text-center font-semibold text-lg">
                Sign In
              </Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Sign Up Link */}
        <View className="flex-row justify-center mt-8">
          <Text className="text-gray-400">Don't have an account? </Text>
          <Link href="/(auth)/signup" asChild>
            <TouchableOpacity>
              <Text className="text-cyan-400 font-semibold">Sign Up</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}
