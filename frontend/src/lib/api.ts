import { ChatMessage, ChatRequest, ChatResponse, HealthResponse } from '@/types/chat';
import { ChunkedDocumentResponse, DocumentExtractionResponse } from '@/types/document';
import { Conversation, Message, Citation, StoredDocument, WaitlistSubmissionResult, SubscriptionStatus, FullCurriculumResponse, SubjectDetailResponse } from '@/types/database';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

function getAuthHeaders(token?: string): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// =============================================================================
// Waitlist API
// =============================================================================

export async function submitWaitlist(
  fullName: string,
  email: string,
  institution?: string
): Promise<WaitlistSubmissionResult> {
  const res = await fetch(`${API_BASE_URL}/waitlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      full_name: fullName,
      email,
      institution: institution || null,
    }),
  });

  if (!res.ok) {
    let errorDetail = `Waitlist submission failed (${res.status})`;
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

// =============================================================================
// Persistent Conversations API
// =============================================================================

export async function createConversation(
  title: string = 'New Academic Conversation',
  token?: string
): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/conversations`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ title }),
  });

  if (!res.ok) {
    throw new Error(`Failed to create conversation (${res.status})`);
  }
  return res.json();
}

export async function listConversations(token?: string): Promise<Conversation[]> {
  const res = await fetch(`${API_BASE_URL}/conversations`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Failed to load conversations (${res.status})`);
  }
  return res.json();
}

export async function getConversation(
  conversationId: string,
  token?: string
): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Failed to load conversation (${res.status})`);
  }
  return res.json();
}

export async function renameConversation(
  conversationId: string,
  title: string,
  token?: string
): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ title }),
  });

  if (!res.ok) {
    throw new Error(`Failed to rename conversation (${res.status})`);
  }
  return res.json();
}

export async function deleteConversation(
  conversationId: string,
  token?: string
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Failed to delete conversation (${res.status})`);
  }
}

export async function sendConversationMessage(
  conversationId: string,
  content: string,
  token?: string
): Promise<{
  user_message: Message;
  assistant_message: Message;
  conversation_id: string;
  remaining_credits?: number;
  is_paid?: boolean;
  citations?: Citation[];
}> {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ content }),
  });

  if (!res.ok) {
    let errorDetail = `Message send failed (${res.status})`;
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

// =============================================================================
// Authenticated Document Storage API
// =============================================================================

export async function uploadDocumentAuthenticated(
  file: File,
  token?: string,
  scope: 'personal' | 'shared' = 'personal',
  semesterId?: string,
  subjectId?: string,
  unitId?: string
): Promise<{ document: StoredDocument; total_pages: number; total_chunks: number; status: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const queryParams = new URLSearchParams({ scope });
  if (semesterId) queryParams.set('semester_id', semesterId);
  if (subjectId) queryParams.set('subject_id', subjectId);
  if (unitId) queryParams.set('unit_id', unitId);

  const res = await fetch(`${API_BASE_URL}/documents/upload?${queryParams.toString()}`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!res.ok) {
    let errorDetail = `Upload failed (${res.status})`;
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function listDocuments(token?: string): Promise<StoredDocument[]> {
  const res = await fetch(`${API_BASE_URL}/documents`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Failed to list documents (${res.status})`);
  }
  return res.json();
}

export async function getDocumentDownloadUrl(
  documentId: string,
  token?: string
): Promise<{ document_id: string; filename: string; signed_url: string; expires_in_seconds: number }> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/download`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Failed to get document download URL (${res.status})`);
  }
  return res.json();
}

// =============================================================================
// Existing Chat & Extraction Functions (Preserved for compatibility)
// =============================================================================

export async function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
  visitorSessionId?: string
): Promise<ChatResponse> {
  const payload: ChatRequest = {
    message,
    history,
    temperature: 0.7,
  };

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (visitorSessionId) {
    headers['X-Visitor-Session-Id'] = visitorSessionId;
  }

  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorDetail = `Backend HTTP error: ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || errorDetail;
    } catch {
      // Fallback
    }
    const err = new Error(errorDetail) as Error & { status?: number; limitReached?: boolean };
    err.status = response.status;
    if (response.status === 429) {
      err.limitReached = true;
    }
    throw err;
  }

  return response.json();
}

export async function checkBackendHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/health`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }

  return response.json();
}

export async function extractDocumentText(file: File): Promise<DocumentExtractionResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/extract`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = `Extraction failed with status: ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function chunkDocument(
  file: File,
  targetTokens?: number,
  overlapTokens?: number
): Promise<ChunkedDocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const queryParams = new URLSearchParams();
  if (targetTokens !== undefined) {
    queryParams.append('target_tokens', targetTokens.toString());
  }
  if (overlapTokens !== undefined) {
    queryParams.append('overlap_tokens', overlapTokens.toString());
  }

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';

  const response = await fetch(`${API_BASE_URL}/documents/chunk${queryString}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = `Chunking failed with status: ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

// =============================================================================
// Student Profile & Credits API
// =============================================================================

export async function getMyProfile(token?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/profile`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to load profile (${res.status})`);
  return res.json();
}

export async function updateMyProfile(
  payload: { full_name?: string; institution?: string },
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/profile`, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to update profile (${res.status})`);
  return res.json();
}

export async function getCreditBalance(token?: string): Promise<{
  credits_balance: number;
  is_paid_subscriber: boolean;
  plan: string;
  threshold_warning: boolean;
  is_exhausted: boolean;
}> {
  const res = await fetch(`${API_BASE_URL}/credits`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to check credits (${res.status})`);
  return res.json();
}

export async function getCreditHistory(token?: string): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/credits/history`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to load credit history (${res.status})`);
  return res.json();
}

// =============================================================================
// Razorpay Payments & Subscriptions API
// =============================================================================

export async function createPaymentOrder(
  plan: 'monthly' | 'yearly',
  token?: string
): Promise<{
  order_id: string;
  amount_paise: number;
  currency: string;
  key_id: string;
  plan: string;
}> {
  const res = await fetch(`${API_BASE_URL}/payments/create-order`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan }),
  });
  if (!res.ok) {
    let msg = `Order creation failed (${res.status})`;
    try {
      const err = await res.json();
      msg = err.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function verifyPayment(
  payload: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  },
  token?: string
): Promise<{ status: string; message: string; plan: string; subscription: any }> {
  const res = await fetch(`${API_BASE_URL}/payments/verify`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let msg = `Payment verification failed (${res.status})`;
    try {
      const err = await res.json();
      msg = err.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function getCurrentSubscription(token?: string): Promise<SubscriptionStatus> {
  const res = await fetch(`${API_BASE_URL}/payments/subscription`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to load subscription (${res.status})`);
  return res.json();
}

export async function getPaymentHistory(token?: string): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/payments/history`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to load payment history (${res.status})`);
  return res.json();
}

// =============================================================================
// Administrative Dashboard API
// =============================================================================

export async function getPlatformMetrics(token?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/admin/metrics`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to load admin metrics (${res.status})`);
  return res.json();
}

export async function listAdminStudents(search?: string, token?: string): Promise<any[]> {
  const qs = search ? `?search=${encodeURIComponent(search)}` : '';
  const res = await fetch(`${API_BASE_URL}/admin/students${qs}`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to list students (${res.status})`);
  return res.json();
}

export async function createStudentAccount(
  payload: {
    email: string;
    password: string;
    full_name: string;
    institution?: string;
    role?: string;
  },
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/admin/students`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let msg = `Student creation failed (${res.status})`;
    try {
      const err = await res.json();
      msg = err.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function updateStudentStatus(
  studentId: string,
  status: 'active' | 'suspended' | 'deactivated',
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/admin/students/${studentId}/status`, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error(`Failed to update student status (${res.status})`);
  return res.json();
}

export async function assignStudentPlan(
  studentId: string,
  plan: 'monthly' | 'yearly',
  days: number,
  reason: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/admin/students/${studentId}/plan`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan, days, reason }),
  });
  if (!res.ok) throw new Error(`Failed to assign plan (${res.status})`);
  return res.json();
}

export async function listAdminPayments(token?: string): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/admin/payments`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to load payments (${res.status})`);
  return res.json();
}

export async function listAdminSubscriptions(token?: string): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/admin/subscriptions`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to load subscriptions (${res.status})`);
  return res.json();
}

export async function resolveSubscription(
  studentId: string,
  plan: 'monthly' | 'yearly',
  days: number,
  reason: string,
  token?: string
): Promise<any> {
  const qs = new URLSearchParams({
    student_id: studentId,
    plan,
    days: days.toString(),
    reason,
  });
  const res = await fetch(`${API_BASE_URL}/admin/subscriptions/resolve?${qs.toString()}`, {
    method: 'POST',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to resolve subscription (${res.status})`);
  return res.json();
}

export async function listAdminWaitlist(status?: string, token?: string): Promise<any[]> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  const res = await fetch(`${API_BASE_URL}/admin/waitlist${qs}`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to load waitlist (${res.status})`);
  return res.json();
}

export async function updateWaitlistStatus(
  entryId: string,
  status: 'pending' | 'approved' | 'rejected' | 'contacted',
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/admin/waitlist/${entryId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error(`Failed to update waitlist entry (${res.status})`);
  return res.json();
}

export async function deleteSharedDocument(documentId: string, token?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/admin/documents/${documentId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to delete shared document (${res.status})`);
  return res.json();
}

export async function deletePersonalDocument(documentId: string, token?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    let errorDetail = `Failed to delete document (${res.status})`;
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function deleteMyAccount(token?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/account/me`, {
    method: 'DELETE',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    let errorDetail = `Failed to delete account (${res.status})`;
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function deleteAdminStudent(studentId: string, token?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/admin/students/${studentId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    let errorDetail = `Failed to delete student account (${res.status})`;
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

// =============================================================================
// Academic Curriculum & Syllabus Functions (Semesters V & VI)
// =============================================================================

export async function getCurriculum(token?: string): Promise<FullCurriculumResponse> {
  const res = await fetch(`${API_BASE_URL}/academic/curriculum`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    let errorDetail = `Failed to fetch curriculum (${res.status})`;
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function getSubjectDetail(subjectId: string, token?: string): Promise<SubjectDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/academic/subjects/${subjectId}`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    let errorDetail = `Failed to fetch subject details (${res.status})`;
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // Fallback
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function getSubjectDocuments(subjectId: string, token?: string): Promise<StoredDocument[]> {
  const res = await fetch(`${API_BASE_URL}/academic/subjects/${subjectId}/documents`, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    return [];
  }
  return res.json();
}


