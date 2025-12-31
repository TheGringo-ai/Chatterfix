/**
 * Frontend AI Service
 * Communicates with the backend AI API
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:3001');

class AIService {
  /**
   * Generate training content
   * @param {string} prompt - Training content prompt
   * @param {object} context - RAG context and employee data
   * @param {object} options - Generation options
   */
  async generateTrainingContent(prompt, context = {}, options = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/generate-training`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          context,
          options,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to generate training content');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('AI Service - Generate Training Error:', error);
      throw error;
    }
  }

  /**
   * Generate quiz questions
   * @param {string} content - Training content
   * @param {number} questionCount - Number of questions
   * @param {object} options - Options including provider
   */
  async generateQuiz(content, questionCount = 5, options = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/generate-quiz`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          questionCount,
          options,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to generate quiz');
      }

      const data = await response.json();
      return data.data.questions;
    } catch (error) {
      console.error('AI Service - Generate Quiz Error:', error);
      throw error;
    }
  }

  /**
   * Translate content
   * @param {string} content - Content to translate
   * @param {string} targetLanguage - Target language code
   * @param {object} options - Options including provider
   */
  async translateContent(content, targetLanguage, options = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          targetLanguage,
          options,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to translate content');
      }

      const data = await response.json();
      return data.data.translatedContent;
    } catch (error) {
      console.error('AI Service - Translate Error:', error);
      throw error;
    }
  }

  /**
   * Analyze employee performance
   * @param {object} employeeData - Employee training data
   * @param {object} options - Options including provider
   */
  async analyzePerformance(employeeData, options = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/analyze-performance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          employeeData,
          options,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to analyze performance');
      }

      const data = await response.json();
      return data.data.analysis;
    } catch (error) {
      console.error('AI Service - Analyze Performance Error:', error);
      throw error;
    }
  }

  /**
   * Generate safety content
   * @param {string} scenario - Safety scenario
   * @param {object} context - Additional context
   * @param {object} options - Options including provider
   */
  async generateSafetyContent(scenario, context = {}, options = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/safety-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scenario,
          context,
          options,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to generate safety content');
      }

      const data = await response.json();
      return data.data.content;
    } catch (error) {
      console.error('AI Service - Safety Content Error:', error);
      throw error;
    }
  }

  /**
   * Generate embeddings for RAG
   * @param {string[]} texts - Array of text chunks
   */
  async generateEmbeddings(texts) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/embeddings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          texts,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to generate embeddings');
      }

      const data = await response.json();
      return data.data.embeddings;
    } catch (error) {
      console.error('AI Service - Generate Embeddings Error:', error);
      throw error;
    }
  }

  /**
   * Get available AI providers
   */
  async getProviders() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/providers`);

      if (!response.ok) {
        throw new Error('Failed to fetch providers');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('AI Service - Get Providers Error:', error);
      throw error;
    }
  }

  /**
   * Health check for all AI providers
   */
  async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/health`);
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('AI Service - Health Check Error:', error);
      throw error;
    }
  }

  /**
   * Health check for specific provider
   * @param {string} provider - Provider name
   */
  async healthCheckProvider(provider) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/health/${provider}`);
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error(`AI Service - Health Check ${provider} Error:`, error);
      throw error;
    }
  }

  /**
   * Get recommended provider for task
   * @param {string} taskType - Type of task
   */
  async getRecommendedProvider(taskType) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/recommend/${taskType}`);
      const data = await response.json();
      return data.data.recommendedProvider;
    } catch (error) {
      console.error('AI Service - Get Recommendation Error:', error);
      throw error;
    }
  }
}

export default new AIService();
