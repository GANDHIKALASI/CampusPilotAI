/**
 * Document extraction and chunking contracts matching backend Pydantic schemas.
 */

export interface ExtractedPage {
  page_number: number;
  content: string;
  character_count: number;
  has_text: boolean;
}

export interface DocumentExtractionResponse {
  filename: string;
  total_pages: number;
  extracted_pages: number;
  file_size_bytes: number;
  pages: ExtractedPage[];
  status: string;
}

export interface DocumentChunk {
  chunk_index: number;
  page_number: number;
  filename: string;
  content: string;
  token_count: number;
  character_count: number;
  start_char_offset: number;
  end_char_offset: number;
  document_id?: string | null;
}

export interface ChunkedDocumentResponse {
  filename: string;
  total_pages: number;
  total_chunks: number;
  target_chunk_tokens: number;
  overlap_tokens: number;
  chunks: DocumentChunk[];
  status: string;
}
