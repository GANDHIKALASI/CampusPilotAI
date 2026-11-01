"use client";

import React, { useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Citation } from "@/types/database";

interface MarkdownRendererProps {
  content: string;
  citations?: Citation[];
  onSelectCitation?: (citation: Citation) => void;
}

export function MarkdownRenderer({ content, citations, onSelectCitation }: MarkdownRendererProps) {
  // Convert valid verified citation tokens [S1], [Source S1] to internal anchors
  const processedContent = useMemo(() => {
    if (!content || !citations || citations.length === 0) return content;

    const validSourceIds = new Set(citations.map((c) => c.source_id.toUpperCase()));

    // Match [S1], [Source S1], [Source: S1]
    return content.replace(/\[(?:Source:?\s*)?(S\d+)(?::[^\]]*)?\]/gi, (match, sid) => {
      const cleanId = sid.toUpperCase();
      if (validSourceIds.has(cleanId)) {
        return `[${cleanId}](#citation-${cleanId})`;
      }
      return match;
    });
  }, [content, citations]);

  return (
    <div className="markdown-content text-sm leading-relaxed text-stone-800">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h1 className="mt-4 mb-2 text-xl font-bold tracking-tight text-stone-900 border-b border-stone-200/80 pb-1.5 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="mt-4 mb-2 text-lg font-semibold tracking-tight text-stone-900 first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mt-3 mb-1.5 text-base font-semibold text-stone-900 first:mt-0">
              {children}
            </h3>
          ),

          // Paragraphs
          p: ({ children }) => (
            <p className="my-2 text-sm leading-relaxed text-stone-800 last:mb-0">
              {children}
            </p>
          ),

          // Lists
          ul: ({ children }) => (
            <ul className="my-2.5 list-disc pl-5 space-y-1 text-stone-800 marker:text-stone-400">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="my-2.5 list-decimal pl-5 space-y-1 text-stone-800 marker:text-stone-500 font-medium [&>li>span]:font-normal">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="pl-1 leading-relaxed text-sm text-stone-800">
              {children}
            </li>
          ),

          // Bold & Italic
          strong: ({ children }) => (
            <strong className="font-semibold text-stone-900">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic text-stone-700">{children}</em>
          ),

          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="my-3 border-l-3 border-stone-300 bg-stone-50/70 pl-3.5 py-1.5 text-stone-700 italic rounded-r-md">
              {children}
            </blockquote>
          ),

          // Horizontal rule
          hr: () => <hr className="my-4 border-stone-200" />,

          // Links & Interactive Citations
          a: ({ href, children }) => {
            if (href?.startsWith("#citation-")) {
              const sid = href.replace("#citation-", "").toUpperCase();
              const matched = citations?.find((c) => c.source_id.toUpperCase() === sid);
              if (matched && onSelectCitation) {
                return (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      onSelectCitation(matched);
                    }}
                    className="inline-flex items-center gap-0.5 mx-0.5 px-1.5 py-0.5 rounded-md border border-emerald-300 bg-emerald-50 text-[11px] font-semibold text-emerald-800 hover:bg-emerald-100 hover:border-emerald-400 transition-colors cursor-pointer align-baseline shadow-2xs"
                    title={`Source ${matched.source_id}: ${matched.filename} (Page ${matched.page_number})`}
                  >
                    <span>[{matched.source_id}]</span>
                  </button>
                );
              }
              return <span className="font-medium text-emerald-800">[{sid}]</span>;
            }

            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-stone-900 underline decoration-stone-400 decoration-1 underline-offset-2 transition-colors hover:text-stone-600 hover:decoration-stone-600"
              >
                {children}
                <span className="inline-block ml-0.5 text-[10px] text-stone-400">↗</span>
              </a>
            );
          },

          // Code blocks & Inline code
          code: ({ className, children, ...props }) => {
            const isCodeBlock = Boolean(className);
            const language = className ? className.replace("language-", "") : "";

            if (!isCodeBlock) {
              return (
                <code
                  className="rounded-md border border-stone-200 bg-stone-100/90 px-1.5 py-0.5 font-mono text-[12.5px] font-medium text-stone-800"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            return (
              <CodeBlock language={language} code={String(children).replace(/\n$/, "")} />
            );
          },

          // Tables (GFM)
          table: ({ children }) => (
            <div className="my-3.5 overflow-x-auto rounded-lg border border-stone-200 bg-white shadow-2xs">
              <table className="w-full text-left text-xs border-collapse">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="border-b border-stone-200 bg-stone-50/80 text-stone-800">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-stone-100 text-stone-700">
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="transition-colors hover:bg-stone-50/50">{children}</tr>
          ),
          th: ({ children }) => (
            <th className="px-3.5 py-2.5 font-semibold text-stone-900">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3.5 py-2.5 leading-relaxed">{children}</td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function CodeBlock({ language, code }: { language?: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3 overflow-hidden rounded-xl border border-stone-800 bg-[#18181B] text-stone-100 shadow-xs">
      <div className="flex items-center justify-between border-b border-stone-800 bg-[#27272A]/70 px-3.5 py-1.5 text-xs text-stone-400">
        <span className="font-mono text-[11px] tracking-wider uppercase text-stone-400">
          {language || "code"}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] font-medium text-stone-300 transition-colors hover:text-white"
        >
          {copied ? (
            <>
              <svg className="h-3 w-3 text-emerald-400" viewBox="0 0 16 16" fill="currentColor">
                <path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z" />
              </svg>
              <span>Copied</span>
            </>
          ) : (
            <>
              <svg className="h-3 w-3" viewBox="0 0 16 16" fill="currentColor">
                <path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z" />
                <path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z" />
              </svg>
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-3.5 font-mono text-[13px] leading-relaxed text-stone-200">
        <code>{code}</code>
      </pre>
    </div>
  );
}
