/**
 * CampusPilot AI Data Contracts
 * Mirrored 1:1 with backend FastAPI schemas in app/schemas/chat.py
 */

export type MessageRole = 'user' | 'model' | 'system';

export interface ChatMessage {
  role: MessageRole;
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  history?: ChatMessage[];
  temperature?: number;
  model?: string | null;
}

export interface ChatResponse {
  reply: string;
  model: string;
  timestamp: string;
  status: string;
  remaining_messages?: number;
  visitor_limit?: number;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  gemini_configured: boolean;
}
