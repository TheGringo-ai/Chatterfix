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
  ScrollView,
} from 'react-native';
import { Link, router } from 'expo-router';
import { authService } from '@/services/authService';
import { useAppStore } from '@/stores/appStore';

export default function SignupScreen() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const setOrganizationId = useAppStore((state) => state.setOrganizationId);

  const handleSignup = async () => {
    if (!fullName || !email || !password || !confirmPassword) {
      Alert.alert('Error', 'Please fill in all fields.');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match.');
      return;
    }

    if (password.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    try {
      const userData = await authService.signUp(email, password, fullName);
      if (userData.organizationId) {
        setOrganizationId(userData.organizationId);
      }
      router.replace('/');
    } catch (error: any) {
      Alert.alert('Sign Up Failed', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-gray-900"
    >
      <ScrollView
        contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }}
        keyboardShouldPersistTaps="handled"
      >
        <View className="flex-1 justify-center px-8 py-12">
          {/* Logo/Title */}
          <View className="items-center mb-10">
            <Text className="text-4xl font-bold text-cyan-400">ChatterFix</Text>
            <Text className="text-lg text-gray-400 mt-2">Create Account</Text>
          </View>

          {/* Signup Form */}
          <View className="space-y-4">
            <View>
              <Text className="text-gray-400 mb-2">Full Name</Text>
              <TextInput
                className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700"
                placeholder="Enter your full name"
                placeholderTextColor="#6B7280"
                value={fullName}
                onChangeText={setFullName}
                autoComplete="name"
              />
            </View>

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
                placeholder="Create a password (6+ characters)"
                placeholderTextColor="#6B7280"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoComplete="password-new"
              />
            </View>

            <View>
              <Text className="text-gray-400 mb-2">Confirm Password</Text>
              <TextInput
                className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700"
                placeholder="Confirm your password"
                placeholderTextColor="#6B7280"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry
                autoComplete="password-new"
              />
            </View>

            <TouchableOpacity
              className={`bg-cyan-500 py-4 rounded-lg mt-4 ${
                loading ? 'opacity-50' : ''
              }`}
              onPress={handleSignup}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text className="text-white text-center font-semibold text-lg">
                  Create Account
                </Text>
              )}
            </TouchableOpacity>
          </View>

          {/* Sign In Link */}
          <View className="flex-row justify-center mt-8">
            <Text className="text-gray-400">Already have an account? </Text>
            <Link href="/(auth)/login" asChild>
              <TouchableOpacity>
                <Text className="text-cyan-400 font-semibold">Sign In</Text>
              </TouchableOpacity>
            </Link>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
