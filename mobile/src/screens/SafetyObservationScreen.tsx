/**
 * SafetyObservationScreen - Submit Safety Observations
 *
 * Captures behavioral observations for:
 * - Safe behaviors (positive recognition)
 * - At-risk behaviors
 * - Unsafe conditions
 * - Near-miss events
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

type ObservationType = 'safe_behavior' | 'at_risk_behavior' | 'unsafe_condition' | 'near_miss' | 'suggestion';

interface ObservationTypeOption {
  id: ObservationType;
  label: string;
  icon: string;
  description: string;
  color: string;
}

const observationTypes: ObservationTypeOption[] = [
  { id: 'safe_behavior', label: 'Safe Behavior', icon: '✅', description: 'Recognize safe actions', color: '#27ae60' },
  { id: 'at_risk_behavior', label: 'At-Risk Behavior', icon: '⚠️', description: 'Potentially unsafe action', color: '#f39c12' },
  { id: 'unsafe_condition', label: 'Unsafe Condition', icon: '🚫', description: 'Hazardous condition found', color: '#e74c3c' },
  { id: 'near_miss', label: 'Near Miss', icon: '😰', description: 'Close call event', color: '#9b59b6' },
  { id: 'suggestion', label: 'Suggestion', icon: '💡', description: 'Safety improvement idea', color: '#3498db' },
];

const categoryOptions = [
  'PPE Compliance',
  'Housekeeping',
  'Equipment Safety',
  'Ergonomics',
  'Chemical Handling',
  'Electrical Safety',
  'Fall Protection',
  'Fire Safety',
  'Traffic/Pedestrian',
  'Lockout/Tagout',
  'Other',
];

export default function SafetyObservationScreen() {
  const navigation = useNavigation<any>();
  const { user, isAuthenticated } = useAuth();

  const [selectedType, setSelectedType] = useState<ObservationType | null>(null);
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [personObserved, setPersonObserved] = useState('');
  const [coachingProvided, setCoachingProvided] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!selectedType) {
      Alert.alert('Required', 'Please select an observation type');
      return;
    }
    if (!description.trim()) {
      Alert.alert('Required', 'Please describe what you observed');
      return;
    }
    if (!location.trim()) {
      Alert.alert('Required', 'Please enter the location');
      return;
    }

    try {
      setSubmitting(true);

      const observationData = {
        observation_type: selectedType,
        description,
        location,
        category: selectedCategory,
        person_observed: personObserved || null,
        coaching_provided: coachingProvided,
        observed_at: new Date().toISOString(),
        photos: [],
      };

      const response = await api.post('/safety/observations', observationData);

      if (response.data?.success) {
        Alert.alert(
          'Observation Submitted',
          selectedType === 'safe_behavior'
            ? 'Great job recognizing safe behavior! This helps build a positive safety culture.'
            : 'Thank you for your observation. It helps make our workplace safer.',
          [
            {
              text: 'OK',
              onPress: () => navigation.goBack(),
            },
          ]
        );
      } else {
        throw new Error('Failed to submit');
      }
    } catch (error) {
      console.error('Failed to submit observation:', error);
      Alert.alert(
        'Submitted (Demo)',
        'In demo mode - observation would be logged to the system.',
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Safety Observation</Text>
          <Text style={styles.headerSubtitle}>
            See something? Say something. Every observation matters.
          </Text>
        </View>

        {/* Observation Type Selection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>What did you observe?</Text>
          <View style={styles.typeGrid}>
            {observationTypes.map((type) => (
              <TouchableOpacity
                key={type.id}
                style={[
                  styles.typeCard,
                  selectedType === type.id && { borderColor: type.color, backgroundColor: `${type.color}20` },
                ]}
                onPress={() => setSelectedType(type.id)}
              >
                <Text style={styles.typeIcon}>{type.icon}</Text>
                <Text style={styles.typeLabel}>{type.label}</Text>
                <Text style={styles.typeDescription}>{type.description}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Category Selection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Category</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.categoryContainer}
          >
            {categoryOptions.map((category) => (
              <TouchableOpacity
                key={category}
                style={[
                  styles.categoryChip,
                  selectedCategory === category && styles.categoryChipSelected,
                ]}
                onPress={() => setSelectedCategory(category === selectedCategory ? null : category)}
              >
                <Text
                  style={[
                    styles.categoryChipText,
                    selectedCategory === category && styles.categoryChipTextSelected,
                  ]}
                >
                  {category}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Description */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Description *</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Describe what you observed in detail..."
            placeholderTextColor="#666"
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />
        </View>

        {/* Location */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Location *</Text>
          <TextInput
            style={styles.input}
            placeholder="Where did this occur? (e.g., Building A, Line 2)"
            placeholderTextColor="#666"
            value={location}
            onChangeText={setLocation}
          />
        </View>

        {/* Person Observed (Optional) */}
        {(selectedType === 'safe_behavior' || selectedType === 'at_risk_behavior') && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Person Observed (Optional)</Text>
            <TextInput
              style={styles.input}
              placeholder="Name (for recognition or coaching)"
              placeholderTextColor="#666"
              value={personObserved}
              onChangeText={setPersonObserved}
            />
            <Text style={styles.helperText}>
              {selectedType === 'safe_behavior'
                ? 'Name the person to give them recognition!'
                : 'For coaching purposes only - not punitive'}
            </Text>
          </View>
        )}

        {/* Coaching Provided Toggle */}
        {selectedType === 'at_risk_behavior' && (
          <View style={styles.toggleContainer}>
            <View style={styles.toggleTextContainer}>
              <Text style={styles.toggleLabel}>Coaching Provided?</Text>
              <Text style={styles.toggleDescription}>
                Did you have a safety conversation with the person?
              </Text>
            </View>
            <Switch
              value={coachingProvided}
              onValueChange={setCoachingProvided}
              trackColor={{ false: '#2d2d4a', true: '#27ae6080' }}
              thumbColor={coachingProvided ? '#27ae60' : '#666'}
            />
          </View>
        )}

        {/* Photo Capture */}
        <TouchableOpacity style={styles.photoButton}>
          <Text style={styles.photoButtonIcon}>📷</Text>
          <Text style={styles.photoButtonText}>Add Photo (Optional)</Text>
        </TouchableOpacity>

        {/* Submit Button */}
        <TouchableOpacity
          style={[
            styles.submitButton,
            submitting && styles.submitButtonDisabled,
            selectedType === 'safe_behavior' && { backgroundColor: '#27ae60' },
          ]}
          onPress={handleSubmit}
          disabled={submitting}
        >
          {submitting ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Text style={styles.submitButtonIcon}>
                {selectedType === 'safe_behavior' ? '🌟' : '👁️'}
              </Text>
              <Text style={styles.submitButtonText}>Submit Observation</Text>
            </>
          )}
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 24,
  },
  headerTitle: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    color: '#a0a0a0',
    fontSize: 14,
    marginTop: 4,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  typeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  typeCard: {
    width: '48%',
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  typeIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  typeLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  typeDescription: {
    color: '#a0a0a0',
    fontSize: 11,
    marginTop: 2,
  },
  categoryContainer: {
    paddingVertical: 4,
  },
  categoryChip: {
    backgroundColor: '#1a1a2e',
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 16,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#2d2d4a',
  },
  categoryChipSelected: {
    backgroundColor: '#3498db',
    borderColor: '#3498db',
  },
  categoryChipText: {
    color: '#a0a0a0',
    fontSize: 13,
  },
  categoryChipTextSelected: {
    color: '#fff',
    fontWeight: '600',
  },
  input: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    color: '#fff',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#2d2d4a',
  },
  textArea: {
    minHeight: 100,
    paddingTop: 16,
  },
  helperText: {
    color: '#a0a0a0',
    fontSize: 12,
    marginTop: 8,
    fontStyle: 'italic',
  },
  toggleContainer: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  toggleTextContainer: {
    flex: 1,
    marginRight: 16,
  },
  toggleLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  toggleDescription: {
    color: '#a0a0a0',
    fontSize: 12,
    marginTop: 2,
  },
  photoButton: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#2d2d4a',
    borderStyle: 'dashed',
  },
  photoButtonIcon: {
    fontSize: 24,
    marginRight: 8,
  },
  photoButtonText: {
    color: '#a0a0a0',
    fontSize: 14,
  },
  submitButton: {
    backgroundColor: '#3498db',
    borderRadius: 12,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});
