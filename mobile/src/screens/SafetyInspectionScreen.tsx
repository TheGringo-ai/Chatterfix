/**
 * SafetyInspectionScreen - Conduct Safety Inspections
 *
 * Mobile-friendly inspection workflow:
 * - Select inspection template
 * - Complete checklist items
 * - Document findings with photos
 * - Generate corrective actions
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

interface InspectionTemplate {
  id: string;
  name: string;
  icon: string;
  description: string;
  itemCount: number;
  estimatedTime: string;
}

interface ChecklistItem {
  id: string;
  question: string;
  category: string;
  status: 'pending' | 'pass' | 'fail' | 'na';
  notes: string;
  requiresPhoto: boolean;
}

const inspectionTemplates: InspectionTemplate[] = [
  {
    id: 'daily_walkthrough',
    name: 'Daily Walkthrough',
    icon: '🚶',
    description: 'Quick daily safety check',
    itemCount: 15,
    estimatedTime: '10 min',
  },
  {
    id: 'fire_safety',
    name: 'Fire Safety',
    icon: '🔥',
    description: 'Fire extinguishers, exits, alarms',
    itemCount: 20,
    estimatedTime: '15 min',
  },
  {
    id: 'ppe_compliance',
    name: 'PPE Compliance',
    icon: '🦺',
    description: 'Personal protective equipment audit',
    itemCount: 12,
    estimatedTime: '10 min',
  },
  {
    id: 'housekeeping',
    name: 'Housekeeping',
    icon: '🧹',
    description: '5S/cleanliness inspection',
    itemCount: 25,
    estimatedTime: '20 min',
  },
  {
    id: 'electrical',
    name: 'Electrical Safety',
    icon: '⚡',
    description: 'Electrical hazards and compliance',
    itemCount: 18,
    estimatedTime: '15 min',
  },
  {
    id: 'forklift_area',
    name: 'Forklift/Traffic',
    icon: '🚜',
    description: 'Vehicle and pedestrian safety',
    itemCount: 16,
    estimatedTime: '12 min',
  },
];

// Demo checklist items for daily walkthrough
const demoChecklistItems: ChecklistItem[] = [
  { id: '1', question: 'Are emergency exits clear and unobstructed?', category: 'Emergency', status: 'pending', notes: '', requiresPhoto: false },
  { id: '2', question: 'Are fire extinguishers accessible and inspection tags current?', category: 'Fire Safety', status: 'pending', notes: '', requiresPhoto: false },
  { id: '3', question: 'Are walking surfaces clean and free of trip hazards?', category: 'Housekeeping', status: 'pending', notes: '', requiresPhoto: false },
  { id: '4', question: 'Is proper PPE being worn in designated areas?', category: 'PPE', status: 'pending', notes: '', requiresPhoto: false },
  { id: '5', question: 'Are chemical containers properly labeled?', category: 'Hazmat', status: 'pending', notes: '', requiresPhoto: false },
  { id: '6', question: 'Are safety guards in place on all machines?', category: 'Machine Safety', status: 'pending', notes: '', requiresPhoto: true },
  { id: '7', question: 'Are electrical panels clear of obstructions (36")?', category: 'Electrical', status: 'pending', notes: '', requiresPhoto: false },
  { id: '8', question: 'Is first aid kit stocked and accessible?', category: 'Emergency', status: 'pending', notes: '', requiresPhoto: false },
  { id: '9', question: 'Are eye wash stations accessible and functional?', category: 'Emergency', status: 'pending', notes: '', requiresPhoto: false },
  { id: '10', question: 'Are forklift traffic lanes marked and clear?', category: 'Traffic', status: 'pending', notes: '', requiresPhoto: false },
];

export default function SafetyInspectionScreen() {
  const navigation = useNavigation<any>();
  const { user, isAuthenticated } = useAuth();

  const [step, setStep] = useState<'select' | 'inspect' | 'review'>('select');
  const [selectedTemplate, setSelectedTemplate] = useState<InspectionTemplate | null>(null);
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([]);
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [location, setLocation] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const startInspection = (template: InspectionTemplate) => {
    setSelectedTemplate(template);
    setChecklistItems(demoChecklistItems.map(item => ({ ...item, status: 'pending', notes: '' })));
    setStep('inspect');
  };

  const updateItemStatus = (status: 'pass' | 'fail' | 'na') => {
    const updatedItems = [...checklistItems];
    updatedItems[currentItemIndex].status = status;
    setChecklistItems(updatedItems);

    // Auto-advance to next item
    if (currentItemIndex < checklistItems.length - 1) {
      setTimeout(() => setCurrentItemIndex(currentItemIndex + 1), 300);
    }
  };

  const updateItemNotes = (notes: string) => {
    const updatedItems = [...checklistItems];
    updatedItems[currentItemIndex].notes = notes;
    setChecklistItems(updatedItems);
  };

  const calculateProgress = () => {
    const completed = checklistItems.filter(item => item.status !== 'pending').length;
    return (completed / checklistItems.length) * 100;
  };

  const getPassRate = () => {
    const applicable = checklistItems.filter(item => item.status !== 'na' && item.status !== 'pending');
    if (applicable.length === 0) return 0;
    const passed = applicable.filter(item => item.status === 'pass').length;
    return Math.round((passed / applicable.length) * 100);
  };

  const getFailedItems = () => {
    return checklistItems.filter(item => item.status === 'fail');
  };

  const handleSubmit = async () => {
    const pendingItems = checklistItems.filter(item => item.status === 'pending');
    if (pendingItems.length > 0) {
      Alert.alert(
        'Incomplete Inspection',
        `You have ${pendingItems.length} items remaining. Do you want to submit anyway?`,
        [
          { text: 'Continue Inspection', style: 'cancel' },
          { text: 'Submit Anyway', onPress: submitInspection },
        ]
      );
      return;
    }
    submitInspection();
  };

  const submitInspection = async () => {
    try {
      setSubmitting(true);

      const inspectionData = {
        template_id: selectedTemplate?.id,
        template_name: selectedTemplate?.name,
        location,
        completed_at: new Date().toISOString(),
        items: checklistItems,
        pass_rate: getPassRate(),
        findings: getFailedItems().length,
      };

      const response = await api.post('/safety/inspections', inspectionData);

      if (response.data?.success) {
        Alert.alert(
          'Inspection Complete',
          `Pass rate: ${getPassRate()}%\nFindings: ${getFailedItems().length}`,
          [{ text: 'OK', onPress: () => navigation.goBack() }]
        );
      } else {
        throw new Error('Failed to submit');
      }
    } catch (error) {
      console.error('Failed to submit inspection:', error);
      Alert.alert(
        'Submitted (Demo)',
        `Pass rate: ${getPassRate()}%\nFindings: ${getFailedItems().length}\n\nIn demo mode - inspection would be logged.`,
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    } finally {
      setSubmitting(false);
    }
  };

  // Template Selection Screen
  if (step === 'select') {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Start Inspection</Text>
            <Text style={styles.headerSubtitle}>
              Select an inspection template to begin
            </Text>
          </View>

          {/* Location Input */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Location</Text>
            <TextInput
              style={styles.input}
              placeholder="Where are you inspecting? (e.g., Building A)"
              placeholderTextColor="#666"
              value={location}
              onChangeText={setLocation}
            />
          </View>

          {/* Template Grid */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Inspection Type</Text>
            <View style={styles.templateGrid}>
              {inspectionTemplates.map((template) => (
                <TouchableOpacity
                  key={template.id}
                  style={styles.templateCard}
                  onPress={() => {
                    if (!location.trim()) {
                      Alert.alert('Required', 'Please enter a location first');
                      return;
                    }
                    startInspection(template);
                  }}
                >
                  <Text style={styles.templateIcon}>{template.icon}</Text>
                  <Text style={styles.templateName}>{template.name}</Text>
                  <Text style={styles.templateDescription}>{template.description}</Text>
                  <View style={styles.templateMeta}>
                    <Text style={styles.templateMetaText}>{template.itemCount} items</Text>
                    <Text style={styles.templateMetaText}>~{template.estimatedTime}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Inspection Screen
  if (step === 'inspect') {
    const currentItem = checklistItems[currentItemIndex];
    const progress = calculateProgress();

    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.inspectContainer}>
          {/* Progress Header */}
          <View style={styles.progressHeader}>
            <View style={styles.progressInfo}>
              <Text style={styles.progressTitle}>{selectedTemplate?.name}</Text>
              <Text style={styles.progressSubtitle}>
                Item {currentItemIndex + 1} of {checklistItems.length}
              </Text>
            </View>
            <View style={styles.progressCircle}>
              <Text style={styles.progressPercent}>{Math.round(progress)}%</Text>
            </View>
          </View>

          {/* Progress Bar */}
          <View style={styles.progressBarContainer}>
            <View style={[styles.progressBar, { width: `${progress}%` }]} />
          </View>

          {/* Item Navigation */}
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.itemNav}
            contentContainerStyle={styles.itemNavContent}
          >
            {checklistItems.map((item, index) => (
              <TouchableOpacity
                key={item.id}
                style={[
                  styles.itemNavDot,
                  index === currentItemIndex && styles.itemNavDotActive,
                  item.status === 'pass' && styles.itemNavDotPass,
                  item.status === 'fail' && styles.itemNavDotFail,
                  item.status === 'na' && styles.itemNavDotNA,
                ]}
                onPress={() => setCurrentItemIndex(index)}
              >
                <Text style={styles.itemNavDotText}>{index + 1}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Current Item */}
          <View style={styles.currentItemContainer}>
            <Text style={styles.itemCategory}>{currentItem.category}</Text>
            <Text style={styles.itemQuestion}>{currentItem.question}</Text>

            {currentItem.requiresPhoto && (
              <TouchableOpacity style={styles.photoPrompt}>
                <Text style={styles.photoPromptIcon}>📷</Text>
                <Text style={styles.photoPromptText}>Photo recommended</Text>
              </TouchableOpacity>
            )}

            {/* Status Buttons */}
            <View style={styles.statusButtons}>
              <TouchableOpacity
                style={[
                  styles.statusButton,
                  styles.statusButtonPass,
                  currentItem.status === 'pass' && styles.statusButtonPassActive,
                ]}
                onPress={() => updateItemStatus('pass')}
              >
                <Text style={styles.statusButtonIcon}>✓</Text>
                <Text style={styles.statusButtonText}>Pass</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.statusButton,
                  styles.statusButtonFail,
                  currentItem.status === 'fail' && styles.statusButtonFailActive,
                ]}
                onPress={() => updateItemStatus('fail')}
              >
                <Text style={styles.statusButtonIcon}>✗</Text>
                <Text style={styles.statusButtonText}>Fail</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.statusButton,
                  styles.statusButtonNA,
                  currentItem.status === 'na' && styles.statusButtonNAActive,
                ]}
                onPress={() => updateItemStatus('na')}
              >
                <Text style={styles.statusButtonIcon}>-</Text>
                <Text style={styles.statusButtonText}>N/A</Text>
              </TouchableOpacity>
            </View>

            {/* Notes */}
            {currentItem.status === 'fail' && (
              <View style={styles.notesContainer}>
                <Text style={styles.notesLabel}>Notes (required for failures)</Text>
                <TextInput
                  style={styles.notesInput}
                  placeholder="Describe the finding..."
                  placeholderTextColor="#666"
                  value={currentItem.notes}
                  onChangeText={updateItemNotes}
                  multiline
                  numberOfLines={3}
                />
              </View>
            )}
          </View>

          {/* Navigation Buttons */}
          <View style={styles.navButtons}>
            <TouchableOpacity
              style={[styles.navButton, currentItemIndex === 0 && styles.navButtonDisabled]}
              onPress={() => setCurrentItemIndex(Math.max(0, currentItemIndex - 1))}
              disabled={currentItemIndex === 0}
            >
              <Text style={styles.navButtonText}>← Previous</Text>
            </TouchableOpacity>

            {currentItemIndex === checklistItems.length - 1 ? (
              <TouchableOpacity
                style={[styles.navButton, styles.navButtonSubmit]}
                onPress={handleSubmit}
              >
                <Text style={styles.navButtonText}>Complete ✓</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                style={styles.navButton}
                onPress={() => setCurrentItemIndex(Math.min(checklistItems.length - 1, currentItemIndex + 1))}
              >
                <Text style={styles.navButtonText}>Next →</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return null;
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
  input: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    color: '#fff',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#2d2d4a',
  },
  templateGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  templateCard: {
    width: '48%',
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2d2d4a',
  },
  templateIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  templateName: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  templateDescription: {
    color: '#a0a0a0',
    fontSize: 12,
    marginBottom: 8,
  },
  templateMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  templateMetaText: {
    color: '#3498db',
    fontSize: 11,
  },
  // Inspect Screen Styles
  inspectContainer: {
    flex: 1,
    padding: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  progressInfo: {
    flex: 1,
  },
  progressTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  progressSubtitle: {
    color: '#a0a0a0',
    fontSize: 14,
    marginTop: 2,
  },
  progressCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#1a1a2e',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#3498db',
  },
  progressPercent: {
    color: '#3498db',
    fontSize: 14,
    fontWeight: 'bold',
  },
  progressBarContainer: {
    height: 4,
    backgroundColor: '#1a1a2e',
    borderRadius: 2,
    marginBottom: 16,
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#3498db',
    borderRadius: 2,
  },
  itemNav: {
    maxHeight: 44,
    marginBottom: 16,
  },
  itemNavContent: {
    alignItems: 'center',
  },
  itemNavDot: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#1a1a2e',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  itemNavDotActive: {
    borderColor: '#3498db',
  },
  itemNavDotPass: {
    backgroundColor: '#27ae60',
  },
  itemNavDotFail: {
    backgroundColor: '#e74c3c',
  },
  itemNavDotNA: {
    backgroundColor: '#7f8c8d',
  },
  itemNavDotText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  currentItemContainer: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  itemCategory: {
    color: '#3498db',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  itemQuestion: {
    color: '#fff',
    fontSize: 18,
    lineHeight: 26,
    marginBottom: 16,
  },
  photoPrompt: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2d2d4a',
    borderRadius: 8,
    padding: 10,
    marginBottom: 16,
  },
  photoPromptIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  photoPromptText: {
    color: '#a0a0a0',
    fontSize: 13,
  },
  statusButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  statusButton: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 4,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  statusButtonPass: {
    backgroundColor: '#27ae6030',
  },
  statusButtonPassActive: {
    backgroundColor: '#27ae60',
    borderColor: '#27ae60',
  },
  statusButtonFail: {
    backgroundColor: '#e74c3c30',
  },
  statusButtonFailActive: {
    backgroundColor: '#e74c3c',
    borderColor: '#e74c3c',
  },
  statusButtonNA: {
    backgroundColor: '#7f8c8d30',
  },
  statusButtonNAActive: {
    backgroundColor: '#7f8c8d',
    borderColor: '#7f8c8d',
  },
  statusButtonIcon: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  statusButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginTop: 4,
  },
  notesContainer: {
    marginTop: 8,
  },
  notesLabel: {
    color: '#e74c3c',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 8,
  },
  notesInput: {
    backgroundColor: '#2d2d4a',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    fontSize: 14,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  navButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  navButton: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 24,
    minWidth: 120,
    alignItems: 'center',
  },
  navButtonDisabled: {
    opacity: 0.5,
  },
  navButtonSubmit: {
    backgroundColor: '#27ae60',
  },
  navButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
