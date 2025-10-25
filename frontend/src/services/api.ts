import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface RecipeURLRequest {
  url: string;
}

export interface Ingredient {
  name: string;
  amount?: string;
  unit?: string;
  notes?: string;
}

export interface PrepStep {
  instruction: string;
  time_estimate?: number;
  category?: string;
}

export interface CookStep {
  step_number: number;
  instruction: string;
  time_estimate?: number;
  parallel_tasks?: string[];
}

export interface OptimizedRecipe {
  title: string;
  ingredients: Ingredient[];
  prep_phase: PrepStep[];
  cook_phase: CookStep[];
  total_time?: number;
  prep_time?: number;
  cook_time?: number;
  servings?: number;
  difficulty?: string;
}

export interface Recipe {
  id: number;
  title: string;
  source_url: string;
  total_time?: number;
  prep_time?: number;
  cook_time?: number;
  servings?: number;
  difficulty?: string;
  created_at: string;
}

export interface CookingSession {
  session_id: number;
  recipe_title: string;
  current_step: string;
  current_phase: string;
  is_active: boolean;
  started_at: string;
}

export interface VoiceCommandRequest {
  command: string;
  session_id: number;
}

export interface VoiceResponse {
  response: string;
  current_step?: string;
  current_phase?: string;
  is_complete?: boolean;
}

// API functions
export const recipeAPI = {
  parseRecipe: async (url: string): Promise<OptimizedRecipe> => {
    const response = await api.post('/parse_recipe', { url });
    return response.data;
  },

  getRecipes: async (): Promise<{ recipes: Recipe[] }> => {
    const response = await api.get('/recipes');
    return response.data;
  },

  getRecipe: async (recipeId: number): Promise<OptimizedRecipe> => {
    const response = await api.get(`/recipe/${recipeId}`);
    return response.data;
  },

  startCooking: async (recipeId: number): Promise<CookingSession> => {
    const response = await api.post(`/start_cooking/${recipeId}`);
    return response.data;
  },

  getCookingSession: async (sessionId: number): Promise<CookingSession> => {
    const response = await api.get(`/cooking_session/${sessionId}`);
    return response.data;
  },

  sendVoiceCommand: async (command: string, sessionId: number): Promise<VoiceResponse> => {
    const response = await api.post('/voice_command', {
      command,
      session_id: sessionId,
    });
    return response.data;
  },
};

export default api;
