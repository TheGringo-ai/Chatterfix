/**
 * Field Mode Context
 *
 * Provides a high-contrast, simplified UI mode for outdoor/field use.
 * Optimized for:
 * - Sunlight readability (light background, dark text)
 * - Large touch targets (gloved hands)
 * - Minimal distractions (no animations)
 * - Essential info only
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StyleSheet } from 'react-native';

const FIELD_MODE_KEY = '@chatterfix_field_mode';

// Standard dark theme (Manager/Office mode)
export const standardTheme = {
  // Backgrounds
  background: '#0c0c0c',
  cardBackground: 'rgba(255, 255, 255, 0.1)',
  headerBackground: '#1e3c72',

  // Text
  textPrimary: '#ffffff',
  textSecondary: 'rgba(255, 255, 255, 0.7)',
  textMuted: 'rgba(255, 255, 255, 0.4)',

  // Accents
  accent: '#3498db',
  success: '#27ae60',
  warning: '#f39c12',
  danger: '#e74c3c',
  critical: '#9b59b6',

  // Borders
  border: 'rgba(255, 255, 255, 0.2)',

  // Status bar
  statusBar: 'light',

  // Animations enabled
  animationsEnabled: true,
};

// High-contrast field theme (Technician/Outdoor mode)
export const fieldTheme = {
  // Backgrounds - Light for sunlight readability
  background: '#f5f5f5',
  cardBackground: '#ffffff',
  headerBackground: '#1a1a1a',

  // Text - High contrast
  textPrimary: '#000000',
  textSecondary: '#333333',
  textMuted: '#666666',

  // Accents - Saturated for visibility
  accent: '#0066cc',
  success: '#008800',
  warning: '#cc6600',
  danger: '#cc0000',
  critical: '#660099',

  // Borders - Visible
  border: '#cccccc',

  // Status bar
  statusBar: 'dark',

  // Animations disabled
  animationsEnabled: false,
};

export type Theme = typeof standardTheme;

interface FieldModeContextType {
  isFieldMode: boolean;
  toggleFieldMode: () => void;
  theme: Theme;
}

const FieldModeContext = createContext<FieldModeContextType>({
  isFieldMode: false,
  toggleFieldMode: () => {},
  theme: standardTheme,
});

export function FieldModeProvider({ children }: { children: ReactNode }) {
  const [isFieldMode, setIsFieldMode] = useState(false);

  // Load saved preference
  useEffect(() => {
    loadFieldModePreference();
  }, []);

  const loadFieldModePreference = async () => {
    try {
      const saved = await AsyncStorage.getItem(FIELD_MODE_KEY);
      if (saved !== null) {
        setIsFieldMode(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Error loading field mode preference:', error);
    }
  };

  const toggleFieldMode = async () => {
    try {
      const newValue = !isFieldMode;
      setIsFieldMode(newValue);
      await AsyncStorage.setItem(FIELD_MODE_KEY, JSON.stringify(newValue));
    } catch (error) {
      console.error('Error saving field mode preference:', error);
    }
  };

  const theme = isFieldMode ? fieldTheme : standardTheme;

  return (
    <FieldModeContext.Provider value={{ isFieldMode, toggleFieldMode, theme }}>
      {children}
    </FieldModeContext.Provider>
  );
}

export function useFieldMode() {
  const context = useContext(FieldModeContext);
  if (!context) {
    throw new Error('useFieldMode must be used within a FieldModeProvider');
  }
  return context;
}

// Utility to create themed styles
export function createThemedStyles<T extends StyleSheet.NamedStyles<T>>(
  styleFactory: (theme: Theme) => T
) {
  return (theme: Theme) => StyleSheet.create(styleFactory(theme));
}

export default FieldModeContext;
