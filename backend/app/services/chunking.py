"""Structure-aware document chunking service for CampusPilot AI.

Partitions cleaned document text into semantic chunks respecting natural
boundaries (sections, paragraphs, sentences, words) while strictly enforcing
intra-page boundaries (chunks never cross PDF pages). Computes exact token
counts and character offsets for citation tracking.
"""

import logging
import re
from functools import lru_cache
from typing import List, Optional, Tuple

from app.core.config import Settings, get_settings
from app.schemas.chunk import ChunkedDocumentResponse, DocumentChunk
from app.schemas.document import DocumentExtractionResponse, ExtractedPage
from app.services.cleaning import TextCleaner, get_text_cleaner

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service responsible for splitting cleaned document text into structured chunks."""

    def __init__(self, settings: Optional[Settings] = None, cleaner: Optional[TextCleaner] = None) -> None:
        self.settings = settings or get_settings()
        self.cleaner = cleaner or get_text_cleaner()
        self._tokenizer = self._init_tokenizer()

    def _init_tokenizer(self):
        """Initialize tiktoken cl100k_base tokenizer with graceful fallback."""
        try:
            import tiktoken
            return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning("Could not load tiktoken cl100k_base encoding: %s. Using heuristic tokenizer.", e)
            return None

    def count_tokens(self, text: str) -> int:
        """Count tokens in string using cl100k_base BPE or character heuristic fallback."""
        if not text:
            return 0
        if self._tokenizer is not None:
            try:
                return len(self._tokenizer.encode(text))
            except Exception:
                pass
        # Heuristic fallback: ~4 characters per token
        return max(1, len(text) // 4)

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences preserving sentence-ending punctuation."""
        # Splits on period, question mark, or exclamation followed by whitespace or newline
        sentence_endings = re.compile(r"(?<=[.!?])\s+")
        parts = sentence_endings.split(text)
        return [p for p in parts if p.strip()]

    def _split_into_atoms(self, text: str) -> List[str]:
        """Break text into fine-grained atomic blocks: paragraphs -> sentences -> words."""
        # First split by double newline (paragraphs / headings)
        paragraphs = text.split("\n\n")
        atoms: List[str] = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If paragraph fits reasonably, keep as single atom
            para_tokens = self.count_tokens(para)
            if para_tokens <= (self.settings.chunk_target_tokens // 2):
                atoms.append(para)
                continue

            # If paragraph is large, split into sentences
            sentences = self._split_into_sentences(para)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                sent_tokens = self.count_tokens(sentence)
                if sent_tokens <= self.settings.chunk_target_tokens:
                    atoms.append(sentence)
                else:
                    # Very long sentence (e.g. uninterrupted code or table), split by words
                    words = sentence.split(" ")
                    current_word_slice: List[str] = []
                    current_slice_tokens = 0

                    for word in words:
                        w_tokens = self.count_tokens(word + " ")
                        if current_slice_tokens + w_tokens > self.settings.chunk_target_tokens and current_word_slice:
                            atoms.append(" ".join(current_word_slice))
                            current_word_slice = [word]
                            current_slice_tokens = w_tokens
                        else:
                            current_word_slice.append(word)
                            current_slice_tokens += w_tokens

                    if current_word_slice:
                        atoms.append(" ".join(current_word_slice))

        return atoms

    def _find_offsets(self, full_page_text: str, chunk_content: str, search_start: int) -> Tuple[int, int]:
        """Find start and end character offsets of chunk content within the page text."""
        # Direct search starting from search_start
        idx = full_page_text.find(chunk_content, search_start)
        if idx != -1:
            return idx, idx + len(chunk_content)

        # Fallback to search from beginning if search_start missed due to overlap
        idx = full_page_text.find(chunk_content)
        if idx != -1:
            return idx, idx + len(chunk_content)

        # Fallback to searching first 40 chars
        prefix = chunk_content[:40]
        idx = full_page_text.find(prefix, search_start)
        if idx != -1:
            return idx, min(len(full_page_text), idx + len(chunk_content))

        # Absolute fallback if exact string was trimmed/reformatted
        return search_start, min(len(full_page_text), search_start + len(chunk_content))

    def chunk_page(
        self,
        cleaned_page_text: str,
        page_number: int,
        filename: str,
        start_chunk_index: int,
        target_tokens: Optional[int] = None,
        overlap_tokens: Optional[int] = None,
    ) -> List[DocumentChunk]:
        """Chunk a single cleaned PDF page into DocumentChunks.

        Strictly enforces intra-page boundaries. Overlap occurs ONLY between
        consecutive chunks of the same page.
        """
        if not cleaned_page_text or not cleaned_page_text.strip():
            return []

        target_limit = target_tokens if target_tokens is not None else self.settings.chunk_target_tokens
        overlap_limit = overlap_tokens if overlap_tokens is not None else self.settings.chunk_overlap_tokens

        total_page_tokens = self.count_tokens(cleaned_page_text)

        # Case 1: Page fits comfortably within target chunk size
        if total_page_tokens <= target_limit:
            chunk = DocumentChunk(
                chunk_index=start_chunk_index,
                page_number=page_number,
                filename=filename,
                content=cleaned_page_text,
                token_count=total_page_tokens,
                character_count=len(cleaned_page_text),
                start_char_offset=0,
                end_char_offset=len(cleaned_page_text),
                document_id=None,
            )
            return [chunk]

        # Case 2: Page exceeds target chunk size -> partition into atoms and assemble with overlap
        atoms = self._split_into_atoms(cleaned_page_text)
        if not atoms:
            return []

        chunks: List[DocumentChunk] = []
        current_chunk_index = start_chunk_index
        atom_index = 0
        search_cursor = 0

        while atom_index < len(atoms):
            chunk_atoms: List[str] = []
            accumulated_tokens = 0

            # Gather atoms until target_limit is reached
            step_idx = atom_index
            while step_idx < len(atoms):
                next_atom = atoms[step_idx]
                separator = "\n\n" if "\n" in next_atom or len(next_atom) > 100 else " "
                cand_text = separator.join(chunk_atoms + [next_atom]) if chunk_atoms else next_atom
                cand_tokens = self.count_tokens(cand_text)

                if cand_tokens <= target_limit or not chunk_atoms:
                    chunk_atoms.append(next_atom)
                    accumulated_tokens = cand_tokens
                    step_idx += 1
                else:
                    break

            if not chunk_atoms:
                # Safety break
                break

            # Join atoms with natural formatting
            # Check if atoms look like paragraphs or sentences
            joined_content = "\n\n".join(chunk_atoms) if any("\n" in a for a in chunk_atoms) else " ".join(chunk_atoms)
            joined_content = joined_content.strip()

            actual_tokens = self.count_tokens(joined_content)
            start_offset, end_offset = self._find_offsets(cleaned_page_text, joined_content, search_cursor)
            search_cursor = start_offset

            chunk = DocumentChunk(
                chunk_index=current_chunk_index,
                page_number=page_number,
                filename=filename,
                content=joined_content,
                token_count=actual_tokens,
                character_count=len(joined_content),
                start_char_offset=start_offset,
                end_char_offset=end_offset,
                document_id=None,
            )
            chunks.append(chunk)
            current_chunk_index += 1

            if step_idx >= len(atoms):
                # Completed all atoms on this page
                break

            # Calculate overlap for next chunk:
            # Backtrack atom_index to include trailing atoms that total approx overlap_limit tokens
            overlap_accum = 0
            backtrack_idx = step_idx - 1
            while backtrack_idx > atom_index:
                atom_tok = self.count_tokens(atoms[backtrack_idx])
                if overlap_accum + atom_tok <= overlap_limit:
                    overlap_accum += atom_tok
                    backtrack_idx -= 1
                else:
                    break

            # Advance atom_index to backtrack_idx + 1 (ensuring forward progress)
            next_start_idx = max(atom_index + 1, backtrack_idx + 1)
            atom_index = next_start_idx

        return chunks

    def chunk_document(
        self,
        extracted_doc: DocumentExtractionResponse,
        target_tokens: Optional[int] = None,
        overlap_tokens: Optional[int] = None,
    ) -> ChunkedDocumentResponse:
        """Clean and chunk an extracted document.

        Iterates page-by-page. Discards empty pages. Assigns sequential global
        chunk indexes while preserving original 1-based page numbers.
        """
        all_chunks: List[DocumentChunk] = []
        global_chunk_counter = 0

        target_limit = target_tokens if target_tokens is not None else self.settings.chunk_target_tokens
        overlap_limit = overlap_tokens if overlap_tokens is not None else self.settings.chunk_overlap_tokens

        for page in extracted_doc.pages:
            # Skip empty pages or pages with no text
            raw_content = getattr(page, "content", getattr(page, "text", ""))
            if not page.has_text or not raw_content or not raw_content.strip():
                continue

            cleaned_text = self.clean_text(raw_content)
            if not cleaned_text:
                continue

            page_chunks = self.chunk_page(
                cleaned_page_text=cleaned_text,
                page_number=page.page_number,
                filename=extracted_doc.filename,
                start_chunk_index=global_chunk_counter,
                target_tokens=target_limit,
                overlap_tokens=overlap_limit,
            )

            all_chunks.extend(page_chunks)
            global_chunk_counter += len(page_chunks)

        return ChunkedDocumentResponse(
            filename=extracted_doc.filename,
            total_pages=extracted_doc.total_pages,
            total_chunks=len(all_chunks),
            target_chunk_tokens=target_limit,
            overlap_tokens=overlap_limit,
            chunks=all_chunks,
            status="success",
        )

    def clean_text(self, text: str) -> str:
        """Helper to invoke underlying TextCleaner."""
        return self.cleaner.clean_text(text)


@lru_cache()
def get_chunking_service() -> ChunkingService:
    """Return cached singleton instance of ChunkingService."""
    return ChunkingService()
