"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  useMemo,
  ReactNode,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import {
  createConversation,
  listConversations,
  getConversation,
  renameConversation,
  deleteConversation,
  sendConversationMessage,
  uploadDocumentAuthenticated,
  listDocuments,
  getDocumentDownloadUrl,
  deletePersonalDocument,
  getMyProfile,
  updateMyProfile,
  getCreditBalance,
  getCurrentSubscription,
  getPaymentHistory,
  deleteMyAccount,
  getCurriculum,
  getSubjectDetail,
} from "@/lib/api";
import {
  Conversation,
  Message,
  StoredDocument,
  StudentProfile,
  SubscriptionStatus,
  CreditStatus,
  PaymentRecord,
  SemesterItem,
  SubjectDetailResponse,
} from "@/types/database";

interface DashboardContextType {
  // Auth
  userEmail: string | null;
  authToken: string | undefined;

  // Profile & Billing
  profile: StudentProfile | null;
  subscription: SubscriptionStatus | null;
  credits: CreditStatus | null;
  payments: PaymentRecord[];
  refreshBillingAndCredits: () => Promise<void>;
  updateProfile: (fullName: string, institution: string) => Promise<void>;

  // Conversations & Chat
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  loading: boolean;
  initialLoading: boolean;
  chatInput: string;
  setChatInput: React.Dispatch<React.SetStateAction<string>>;
  createNewChat: () => Promise<void>;
  selectChat: (id: string) => Promise<void>;
  renameChat: (id: string, newTitle: string) => Promise<void>;
  deleteChat: (id: string) => Promise<void>;
  sendMessage: (customMessage?: string, attachedFile?: File | null) => Promise<void>;

  // Documents
  documents: StoredDocument[];
  refreshDocuments: () => Promise<void>;
  deleteDocument: (docId: string, filename: string) => Promise<void>;
  downloadDocument: (docId: string, filename: string) => Promise<void>;
  askAboutDocument: (doc: StoredDocument) => void;

  // Academic Curriculum
  curriculum: SemesterItem[];
  refreshCurriculum: () => Promise<void>;
  askAboutSubject: (subjectName: string, subjectCode?: string) => void;

  // Modals & Sidebar
  isSidebarOpen: boolean;
  setIsSidebarOpen: React.Dispatch<React.SetStateAction<boolean>>;
  isPricingModalOpen: boolean;
  setIsPricingModalOpen: React.Dispatch<React.SetStateAction<boolean>>;
  showUploadAcademicModal: boolean;
  setShowUploadAcademicModal: React.Dispatch<React.SetStateAction<boolean>>;
  uploadModalFile: File | null;
  setUploadModalFile: React.Dispatch<React.SetStateAction<File | null>>;
  uploadSemesterId: string;
  setUploadSemesterId: React.Dispatch<React.SetStateAction<string>>;
  uploadSubjectId: string;
  setUploadSubjectId: React.Dispatch<React.SetStateAction<string>>;
  uploadUnitId: string;
  setUploadUnitId: React.Dispatch<React.SetStateAction<string>>;
  uploadModalError: string | null;
  setUploadModalError: React.Dispatch<React.SetStateAction<string | null>>;
  uploadModalLoading: boolean;
  openAcademicUploadModal: (initialSubjectId?: string, initialSemesterId?: string) => void;
  handleAcademicModalSubmit: (e: React.FormEvent) => Promise<void>;
  showDeleteAccountModal: boolean;
  setShowDeleteAccountModal: React.Dispatch<React.SetStateAction<boolean>>;
  handleDeleteAccount: (confirmationText: string) => Promise<void>;
  handleLogout: () => Promise<void>;
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export function DashboardProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  // Sidebar
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Auth & Identity
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string | undefined>(undefined);

  // Student Profile, Credits, Subscription & Payments
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [credits, setCredits] = useState<CreditStatus | null>(null);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);

  // Conversations & Chat
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  // Documents
  const [documents, setDocuments] = useState<StoredDocument[]>([]);

  // Modals
  const [isPricingModalOpen, setIsPricingModalOpen] = useState(false);
  const [showDeleteAccountModal, setShowDeleteAccountModal] = useState(false);

  // Academic Curriculum & Upload Modal State
  const [curriculum, setCurriculum] = useState<SemesterItem[]>([]);
  const [showUploadAcademicModal, setShowUploadAcademicModal] = useState(false);
  const [uploadModalFile, setUploadModalFile] = useState<File | null>(null);
  const [uploadSemesterId, setUploadSemesterId] = useState<string>("");
  const [uploadSubjectId, setUploadSubjectId] = useState<string>("");
  const [uploadUnitId, setUploadUnitId] = useState<string>("");
  const [uploadModalError, setUploadModalError] = useState<string | null>(null);
  const [uploadModalLoading, setUploadModalLoading] = useState(false);

  // ===========================================================================
  // 1. Initial Authentication & Lifecycle
  // ===========================================================================
  useEffect(() => {
    const supabase = createClient();

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session || !session.user) {
        router.push("/login?redirectedFrom=" + encodeURIComponent(pathname || "/dashboard"));
        return;
      }
      const email = session.user.email || "Student";
      setUserEmail(email);
      setAuthToken(session.access_token);
      loadInitialData(session.access_token);
    });

    const {
      data: { subscription: authSub },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) {
        router.push("/login");
      } else {
        setAuthToken(session.access_token);
      }
    });

    return () => {
      authSub.unsubscribe();
    };
  }, [router]);

  const loadInitialData = async (token: string) => {
    setInitialLoading(true);
    try {
      // 1. Load Conversations
      const convList = await listConversations(token);
      setConversations(convList);

      if (convList.length > 0) {
        const firstConv = await getConversation(convList[0].id, token);
        setCurrentConversation(firstConv);
        setMessages(firstConv.messages || []);
      } else {
        const newConv = await createConversation("Academic Discussion", token);
        setConversations([newConv]);
        setCurrentConversation(newConv);
        setMessages([]);
      }

      // 2. Load Profile
      const prof = await getMyProfile(token);
      setProfile(prof);

      // 3. Load Billing & Credits
      const [sub, cred, payList] = await Promise.all([
        getCurrentSubscription(token),
        getCreditBalance(token),
        getPaymentHistory(token),
      ]);
      setSubscription(sub);
      setCredits(cred);
      setPayments(payList);

      // 4. Load Documents
      const docs = await listDocuments(token);
      setDocuments(docs);

      // 5. Load Curriculum
      const curr = await getCurriculum(token);
      const semestersList = curr.semesters || [];
      setCurriculum(semestersList);
      if (semestersList.length > 0) {
        setUploadSemesterId(semestersList[0].id);
        if (semestersList[0].subjects && semestersList[0].subjects.length > 0) {
          setUploadSubjectId(semestersList[0].subjects[0].id);
        }
      }
    } catch (err) {
      console.error("Error loading dashboard data:", err);
    } finally {
      setInitialLoading(false);
    }
  };

  const refreshBillingAndCredits = async () => {
    if (!authToken) return;
    try {
      const [sub, cred, payList] = await Promise.all([
        getCurrentSubscription(authToken),
        getCreditBalance(authToken),
        getPaymentHistory(authToken),
      ]);
      setSubscription(sub);
      setCredits(cred);
      setPayments(payList);
    } catch (e) {
      console.error("Failed to refresh billing and credits:", e);
    }
  };

  const refreshDocuments = async () => {
    if (!authToken) return;
    try {
      const docs = await listDocuments(authToken);
      setDocuments(docs);
    } catch (e) {
      console.error("Failed to refresh documents:", e);
    }
  };

  const refreshCurriculum = async () => {
    try {
      const curr = await getCurriculum(authToken);
      setCurriculum(curr.semesters || []);
    } catch (e) {
      console.error("Failed to refresh curriculum:", e);
    }
  };

  const updateProfile = async (fullName: string, institution: string) => {
    if (!authToken) return;
    const updated = await updateMyProfile(
      { full_name: fullName, institution },
      authToken
    );
    setProfile(updated);
  };

  // ===========================================================================
  // 2. Conversation Operations
  // ===========================================================================
  const createNewChat = async () => {
    if (!authToken) return;
    try {
      const newConv = await createConversation("Academic Discussion", authToken);
      setConversations((prev) => [newConv, ...prev]);
      setCurrentConversation(newConv);
      setMessages([]);
      if (pathname !== "/dashboard") {
        router.push("/dashboard");
      }
    } catch (err) {
      console.error("Failed to create new conversation:", err);
    }
  };

  const selectChat = async (id: string) => {
    if (!authToken || currentConversation?.id === id) {
      if (pathname !== "/dashboard") router.push("/dashboard");
      return;
    }
    setLoading(true);
    try {
      const fullConv = await getConversation(id, authToken);
      setCurrentConversation(fullConv);
      setMessages(fullConv.messages || []);
      if (pathname !== "/dashboard") {
        router.push("/dashboard");
      }
    } catch (err) {
      console.error("Failed to fetch conversation:", err);
    } finally {
      setLoading(false);
    }
  };

  const renameChat = async (id: string, newTitle: string) => {
    if (!authToken || !newTitle.trim()) return;
    try {
      const updated = await renameConversation(id, newTitle.trim(), authToken);
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, title: updated.title } : c))
      );
      if (currentConversation?.id === id) {
        setCurrentConversation((prev) => (prev ? { ...prev, title: updated.title } : null));
      }
    } catch (err) {
      console.error("Failed to rename conversation:", err);
    }
  };

  const deleteChat = async (id: string) => {
    if (!authToken) return;
    try {
      await deleteConversation(id, authToken);
      const remaining = conversations.filter((c) => c.id !== id);
      setConversations(remaining);

      if (currentConversation?.id === id) {
        if (remaining.length > 0) {
          selectChat(remaining[0].id);
        } else {
          createNewChat();
        }
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  const sendMessage = async (customMessage?: string, attachedFile?: File | null) => {
    const rawText = customMessage !== undefined ? customMessage : chatInput.trim();
    if ((!rawText && !attachedFile) || loading || !currentConversation || !authToken) return;

    // Credit Check
    if (credits && !credits.is_paid_subscriber && credits.credits_balance <= 0) {
      setIsPricingModalOpen(true);
      return;
    }

    let messageToSend = rawText;

    try {
      if (attachedFile) {
        const uploadRes = await uploadDocumentAuthenticated(attachedFile, authToken, "personal");
        setDocuments((prev) => [uploadRes.document, ...prev]);

        const pdfRefTag = `[Referencing uploaded PDF: ${uploadRes.document.filename}]`;
        if (messageToSend) {
          messageToSend = `${pdfRefTag} ${messageToSend}`;
        } else {
          messageToSend = `${pdfRefTag} Please analyze this document and summarize key concepts.`;
        }
      }

      setChatInput("");
      setLoading(true);

      const tempUserMsg: Message = {
        id: "temp-" + Date.now(),
        conversation_id: currentConversation.id,
        role: "user",
        content: messageToSend,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);

      const updated = await sendConversationMessage(currentConversation.id, messageToSend, authToken);
      const assistantMsg: Message = {
        ...updated.assistant_message,
        citations: updated.citations || [],
      };
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUserMsg.id),
        updated.user_message,
        assistantMsg,
      ]);

      // Refresh credits
      getCreditBalance(authToken).then(setCredits).catch(() => {});
    } catch (err) {
      console.error("Failed to send message:", err);
    } finally {
      setLoading(false);
    }
  };

  // ===========================================================================
  // 3. Document Operations
  // ===========================================================================
  const deleteDocument = async (docId: string, filename: string) => {
    if (!authToken) return;
    if (!confirm(`Are you sure you want to delete "${filename}"? This will permanently delete the PDF and its chunk index.`)) {
      return;
    }
    try {
      await deletePersonalDocument(docId, authToken);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete document.";
      alert(msg);
    }
  };

  const downloadDocument = async (docId: string, filename: string) => {
    if (!authToken) return;
    try {
      const downloadData = await getDocumentDownloadUrl(docId, authToken);
      if (downloadData.signed_url) {
        const a = document.createElement("a");
        a.href = downloadData.signed_url;
        a.download = filename;
        a.target = "_blank";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    } catch (err) {
      alert("Failed to generate download URL.");
    }
  };

  const askAboutDocument = (doc: StoredDocument) => {
    setChatInput(`[Referencing uploaded PDF: ${doc.filename}] Please analyze this document and summarize key concepts.`);
    router.push("/dashboard");
    setTimeout(() => {
      const el = document.getElementById("chat-input");
      if (el) el.focus();
    }, 200);
  };

  // ===========================================================================
  // 4. Academic Curriculum Actions
  // ===========================================================================
  const askAboutSubject = (subjectName: string, subjectCode?: string) => {
    const codeTag = subjectCode ? `(${subjectCode}) ` : "";
    setChatInput(`I want to study ${codeTag}${subjectName}. Please give me a structured syllabus breakdown, core learning objectives, and recommend important exam questions.`);
    router.push("/dashboard");
    setTimeout(() => {
      const el = document.getElementById("chat-input");
      if (el) el.focus();
    }, 200);
  };

  const openAcademicUploadModal = (initialSubjectId?: string, initialSemesterId?: string) => {
    setUploadModalError(null);
    setUploadModalFile(null);
    let targetSemId = initialSemesterId || "";
    let targetSubjId = initialSubjectId || "";

    if (!targetSemId && curriculum.length > 0) {
      targetSemId = curriculum[0].id;
    }
    if (!targetSubjId && targetSemId) {
      const sem = curriculum.find((s) => s.id === targetSemId);
      if (sem && sem.subjects.length > 0) {
        targetSubjId = sem.subjects[0].id;
      }
    }

    setUploadSemesterId(targetSemId);
    setUploadSubjectId(targetSubjId);
    setUploadUnitId("");
    setShowUploadAcademicModal(true);
  };

  const handleAcademicModalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadModalFile) {
      setUploadModalError("Please select a PDF document to upload.");
      return;
    }
    if (uploadModalFile.type !== "application/pdf" && !uploadModalFile.name.toLowerCase().endsWith(".pdf")) {
      setUploadModalError("Only PDF documents are supported.");
      return;
    }

    try {
      setUploadModalLoading(true);
      setUploadModalError(null);
      const uploadRes = await uploadDocumentAuthenticated(
        uploadModalFile,
        authToken,
        "personal",
        uploadSemesterId || undefined,
        uploadSubjectId || undefined,
        uploadUnitId || undefined
      );

      setDocuments((prev) => [uploadRes.document, ...prev]);
      setShowUploadAcademicModal(false);
      setUploadModalFile(null);
      alert(`Document "${uploadModalFile.name}" successfully uploaded and linked to syllabus.`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload document.";
      setUploadModalError(msg);
    } finally {
      setUploadModalLoading(false);
    }
  };

  const handleDeleteAccount = async (confirmationText: string) => {
    if (confirmationText !== "DELETE") {
      throw new Error("Please type DELETE in all uppercase to confirm.");
    }
    if (!authToken) return;
    await deleteMyAccount(authToken);
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login?message=account_deleted");
  };

  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  };

  const value: DashboardContextType = {
    userEmail,
    authToken,
    profile,
    subscription,
    credits,
    payments,
    refreshBillingAndCredits,
    updateProfile,

    conversations,
    currentConversation,
    messages,
    loading,
    initialLoading,
    chatInput,
    setChatInput,
    createNewChat,
    selectChat,
    renameChat,
    deleteChat,
    sendMessage,

    documents,
    refreshDocuments,
    deleteDocument,
    downloadDocument,
    askAboutDocument,

    curriculum,
    refreshCurriculum,
    askAboutSubject,

    isSidebarOpen,
    setIsSidebarOpen,
    isPricingModalOpen,
    setIsPricingModalOpen,
    showUploadAcademicModal,
    setShowUploadAcademicModal,
    uploadModalFile,
    setUploadModalFile,
    uploadSemesterId,
    setUploadSemesterId,
    uploadSubjectId,
    setUploadSubjectId,
    uploadUnitId,
    setUploadUnitId,
    uploadModalError,
    setUploadModalError,
    uploadModalLoading,
    openAcademicUploadModal,
    handleAcademicModalSubmit,
    showDeleteAccountModal,
    setShowDeleteAccountModal,
    handleDeleteAccount,
    handleLogout,
  };

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboard must be used within a DashboardProvider");
  }
  return context;
}
