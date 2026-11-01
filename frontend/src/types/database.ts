/**
 * Database types matching Supabase PostgreSQL tables in CampusPilot AI.
 */

export interface Profile {
  id: string;
  full_name: string;
  avatar_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WaitlistEntry {
  id: string;
  full_name: string;
  email: string;
  institution?: string | null;
  status: 'pending' | 'approved' | 'rejected' | 'contacted';
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface Citation {
  source_id: string;
  document_id: string;
  filename: string;
  page_number: number;
  similarity_score: number;
  chunk_id?: string;
  scope?: string;
  snippet?: string;
  academic_context?: Record<string, any> | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'model' | 'system';
  content: string;
  created_at: string;
  citations?: Citation[];
}

export interface StoredDocument {
  id: string;
  user_id: string;
  filename: string;
  storage_path: string;
  mime_type: string;
  file_size: number;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  scope?: 'personal' | 'shared';
  semester_id?: string | null;
  subject_id?: string | null;
  unit_id?: string | null;
  created_at: string;
  updated_at: string;
}

export * from './academic';

export interface StoredDocumentChunk {
  id: string;
  document_id: string;
  user_id: string;
  chunk_index: number;
  page_number: number;
  content: string;
  token_count: number;
  character_count: number;
  start_char_offset: number;
  end_char_offset: number;
  created_at: string;
}

export interface WaitlistSubmissionResult {
  status: 'success' | 'already_registered';
  message: string;
  data?: WaitlistEntry;
}

export interface StudentProfile {
  id: string;
  email: string;
  full_name: string;
  institution?: string | null;
  avatar_url?: string | null;
  role: 'student' | 'admin';
  status: 'active' | 'suspended' | 'deactivated';
  credits_balance: number;
  plan: 'free' | 'monthly' | 'yearly';
  is_paid: boolean;
}

export interface SubscriptionStatus {
  plan: 'free' | 'monthly' | 'yearly';
  status: 'active' | 'expired' | 'cancelled';
  is_active: boolean;
  is_paid: boolean;
  current_period_start?: string | null;
  current_period_end?: string | null;
  remaining_days?: number | null;
}

export interface CreditStatus {
  credits_balance: number;
  is_paid_subscriber: boolean;
  plan: string;
  threshold_warning: boolean;
  is_exhausted: boolean;
}

export interface CreditTransaction {
  id: string;
  amount: number;
  balance_after: number;
  action: string;
  description?: string | null;
  created_at: string;
}

export interface PaymentRecord {
  id: string;
  user_id: string;
  plan: 'monthly' | 'yearly';
  amount_inr: number;
  currency: string;
  razorpay_order_id: string;
  razorpay_payment_id?: string | null;
  status: 'created' | 'captured' | 'failed' | 'refunded';
  created_at: string;
}

export interface PlatformMetrics {
  total_students: number;
  active_subscriptions: number;
  expired_subscriptions: number;
  total_documents: number;
  total_payments_inr: number;
  total_transactions_count: number;
}

export interface AdminStudentItem {
  id: string;
  email: string;
  full_name: string;
  institution?: string | null;
  role: 'student' | 'admin';
  status: 'active' | 'suspended' | 'deactivated';
  credits_balance: number;
  plan: 'free' | 'monthly' | 'yearly';
  subscription_status: string;
  subscription_expiry?: string | null;
  created_at?: string | null;
}

export interface WaitlistAdminItem {
  id: string;
  full_name: string;
  email: string;
  institution?: string | null;
  status: 'pending' | 'approved' | 'rejected' | 'contacted';
  created_at: string;
}

// Re-export academic types for seamless imports
export * from './academic';

