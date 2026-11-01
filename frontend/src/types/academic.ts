/**
 * Academic curriculum types for BCA Semester V and VI.
 * Grounded in the official BCA syllabus and backend schemas.
 */

import { StoredDocument } from './database';

export interface UnitItem {
  id: string;
  subject_id: string;
  unit_number: number;
  title: string;
  topics: string;
  order_index?: number;
}

export interface PracticalItem {
  id: string;
  subject_id: string;
  exercise_number: number;
  title: string;
  description?: string | null;
  order_index?: number;
}

export interface ProjectReportSection {
  section_number: number;
  title: string;
  description?: string | null;
  required?: boolean;
}

export interface ProjectEvaluationCriteria {
  criteria_number?: number | null;
  criterion?: string | null;
  title?: string | null;
  weight?: string | null;
  description?: string | null;
}

export interface ProjectGuidelinesItem {
  id?: string;
  subject_id?: string;
  title?: string | null;
  description?: string | null;
  report_sections: ProjectReportSection[];
  evaluation_criteria: ProjectEvaluationCriteria[];
}

export interface SubjectItem {
  id: string;
  semester_id: string;
  code?: string | null;
  name: string;
  subject_type: 'theory' | 'practical' | 'project';
  order_index?: number;
  description?: string | null;
  units?: UnitItem[];
  practicals?: PracticalItem[];
  project_guidelines?: ProjectGuidelinesItem | null;
  documents_count?: number;
}

export interface SemesterItem {
  id: string;
  code: string;
  name: string;
  title?: string | null;
  semester_number?: number;
  academic_year?: string;
  order_index?: number;
  description?: string | null;
  subjects: SubjectItem[];
}

export interface FullCurriculumResponse {
  program: string;
  academic_system: string;
  semesters: SemesterItem[];
  status: string;
}

export interface SubjectDetailResponse {
  id: string;
  semester_id: string;
  code?: string | null;
  name: string;
  subject_type: 'theory' | 'practical' | 'project';
  order_index?: number;
  description?: string | null;
  units: UnitItem[];
  practicals: PracticalItem[];
  project_guidelines?: ProjectGuidelinesItem | null;
  documents: StoredDocument[];
  documents_count: number;
  status: string;
}
