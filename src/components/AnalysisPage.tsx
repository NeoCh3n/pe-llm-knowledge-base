import React, { useEffect, useRef, useState } from 'react';
import { Send, Loader2, Search, Brain, Sparkles, GitBranchPlus, BrainCircuit, FileSearch, CheckCircle, XCircle } from 'lucide-react';
import { Message, Document } from '../App';
import { MessageBubble } from './MessageBubble';
import { DocumentSelector } from './DocumentSelector';
import type { Deal } from '../lib/api';
import { getLLMConfig } from '../lib/api';

interface AnalysisPageProps {
  messages: Message[];
  onSendMessage: (
    query: string,
    analysisType: 'document_search' | 'investment_analysis',
    selectedDocIds?: string[]
  ) => Promise<void>;
  onRunWorkflow: (payload: { query: string; doc_ids?: string[]; deal_id?: string }) => Promise<void>;
  isLoading: boolean;
  documents: Document[];
  deals: Deal[];
}

export function AnalysisPage({
  messages,
  onSendMessage,
  onRunWorkflow,
  isLoading,
  documents,
  deals,
}: AnalysisPageProps) {
  const [input, setInput] = useState('');
  const [analysisType, setAnalysisType] = useState<'document_search' | 'investment_analysis'>('investment_analysis');
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string>('');
  const [showDocSelector, setShowDocSelector] = useState(false);
  const [llmStatus, setLlmStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Check LLM connection status
  useEffect(() => {
    getLLMConfig()
      .then((config) => {
        setLlmStatus(config.llm_base_url ? 'connected' : 'disconnected');
      })
      .catch(() => setLlmStatus('disconnected'));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const exampleQueries =
    analysisType === 'investment_analysis'
      ? [
          'Find the closest approved and rejected historical precedents for this software infrastructure deal.',
          'What risks repeatedly appeared in passed deals that look similar to this opportunity?',
          'Compare this opportunity to the firm’s best-performing investments by stage and business model.',
        ]
      : [
          'What was the EBITDA margin in Q4 2024?',
          'Extract the cap table from the memo and keep the table format.',
          'Summarize the key diligence risks with citations.',
        ];

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
          <div className="px-6 py-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-gray-900">Analysis & Precedent Retrieval</h2>
              <p className="text-sm text-gray-500 mt-1">
                {analysisType === 'investment_analysis'
                  ? 'Searches historical deals only. Switch to Document Search to query all document categories.'
                  : 'Use document search for evidence extraction or investment analysis for precedent-aware synthesis.'}
              </p>
            </div>

            <div className="flex items-center gap-2 text-sm">
              {llmStatus === 'checking' ? (
                <><Loader2 size={16} className="animate-spin text-gray-400" /><span className="text-gray-500">Checking LLM...</span></>
              ) : llmStatus === 'connected' ? (
                <><CheckCircle size={16} className="text-green-600" /><span className="text-green-600">LLM Connected</span></>
              ) : (
                <><XCircle size={16} className="text-red-600" /><span className="text-red-600">LLM Not Connected</span></>
              )}
            </div>

            <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setAnalysisType('investment_analysis')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all text-sm ${analysisType === 'investment_analysis' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
              >
                <Brain size={16} />
                Investment Analysis
              </button>
              <button
                onClick={() => setAnalysisType('document_search')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all text-sm ${analysisType === 'document_search' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
              >
                <Search size={16} />
                Document Search
              </button>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 xl:grid-cols-[1fr,280px] gap-4">
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-2">
                <Sparkles size={16} className="text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-900">
                  {analysisType === 'investment_analysis' ? (
                    <>
                      <strong>Institutional memory mode:</strong> bias retrieval toward historical deal documents and use the answer model only for evidence-grounded synthesis.
                    </>
                  ) : (
                    <>
                      <strong>Evidence extraction mode:</strong> search selected documents only and preserve tables and raw excerpts for verification.
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-2 uppercase tracking-wide">Workflow launch</p>
              <select value={selectedDealId} onChange={(e) => setSelectedDealId(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
                <option value="">Optional linked deal</option>
                {deals.map((deal) => (
                  <option key={deal.id} value={deal.id}>
                    {deal.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-6 bg-gray-50">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-2xl">
                <div className="mb-4">
                  {analysisType === 'investment_analysis' ? (
                    <BrainCircuit size={48} className="mx-auto text-gray-300" />
                  ) : (
                    <FileSearch size={48} className="mx-auto text-gray-300" />
                  )}
                </div>
                <h3 className="text-gray-900 mb-2">{analysisType === 'investment_analysis' ? 'Institutional Precedent Search' : 'Document Evidence Search'}</h3>
                <p className="text-sm text-gray-600 mb-6">
                  {analysisType === 'investment_analysis'
                    ? 'Synthesize internal history with explicit citations and no unsupported recommendations.'
                    : 'Retrieve specific facts, tables, and evidence from selected documents.'}
                </p>
                <div className="flex items-center justify-center gap-2 text-sm">
                  {llmStatus === 'checking' && (
                    <>
                      <Loader2 size={16} className="text-gray-400 animate-spin" />
                      <span className="text-gray-500">Checking LLM connection...</span>
                    </>
                  )}
                  {llmStatus === 'connected' && (
                    <>
                      <CheckCircle size={16} className="text-green-600" />
                      <span className="text-green-600">LLM Connected</span>
                    </>
                  )}
                  {llmStatus === 'disconnected' && (
                    <>
                      <XCircle size={16} className="text-red-600" />
                      <span className="text-red-600">LLM Not Connected</span>
                    </>
                  )}
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-4 text-left">
                  <p className="text-sm text-gray-700 mb-3">Example queries:</p>
                  <div className="space-y-2">
                    {exampleQueries.map((query, index) => (
                      <button
                        key={index}
                        onClick={() => setInput(query)}
                        className="w-full text-left px-3 py-2 text-sm text-gray-600 bg-gray-50 hover:bg-blue-50 hover:text-blue-700 rounded border border-gray-200 hover:border-blue-300 transition-colors"
                      >
                        {query}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4 max-w-4xl mx-auto">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="border-t border-gray-200 bg-white px-6 py-4">
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              if (!input.trim() || isLoading) return;
              await onSendMessage(input.trim(), analysisType, analysisType === 'document_search' ? selectedDocIds : undefined);
              setInput('');
            }}
            className="max-w-4xl mx-auto"
          >
            {analysisType === 'document_search' && (
              <div className="mb-3">
                <button type="button" onClick={() => setShowDocSelector(!showDocSelector)} className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
                  {selectedDocIds.length > 0 ? `${selectedDocIds.length} document${selectedDocIds.length > 1 ? 's' : ''} selected` : 'Select documents to search'}
                  <span className="ml-1">{showDocSelector ? '▲' : '▼'}</span>
                </button>
              </div>
            )}

            <div className="flex gap-3 items-end">
              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={async (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if (!input.trim() || isLoading) return;
                      await onSendMessage(input.trim(), analysisType, analysisType === 'document_search' ? selectedDocIds : undefined);
                      setInput('');
                    }
                  }}
                  placeholder={analysisType === 'investment_analysis' ? 'Ask about precedents, rejection patterns, or historical outcomes...' : selectedDocIds.length > 0 ? 'Search selected documents...' : 'Select documents first...'}
                  disabled={isLoading || (analysisType === 'document_search' && selectedDocIds.length === 0)}
                  rows={1}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400 resize-none max-h-32"
                />
              </div>

              <button
                type="button"
                onClick={() =>
                  onRunWorkflow({
                    query: input.trim(),
                    doc_ids: analysisType === 'document_search' ? selectedDocIds : undefined,
                    deal_id: selectedDealId || undefined,
                  })
                }
                disabled={!input.trim() || isLoading}
                className="px-4 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                <GitBranchPlus size={18} />
                Run Workflow
              </button>

              <button
                type="submit"
                disabled={!input.trim() || isLoading || (analysisType === 'document_search' && selectedDocIds.length === 0)}
                className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">Enter sends the query. Run Workflow creates a reusable IC workflow job when the backend endpoint is available.</p>
          </form>
        </div>
      </div>

      {analysisType === 'document_search' && showDocSelector && (
        <DocumentSelector
          documents={documents}
          selectedDocIds={selectedDocIds}
          onToggle={(docId) => {
            setSelectedDocIds((prev) => (prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]));
          }}
          onSelectAll={() => {
            setSelectedDocIds(selectedDocIds.length === documents.length ? [] : documents.map((d) => d.id));
          }}
          onClose={() => setShowDocSelector(false)}
        />
      )}
    </div>
  );
}
