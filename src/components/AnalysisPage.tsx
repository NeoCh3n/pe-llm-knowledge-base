import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Search, Brain, Sparkles } from 'lucide-react';
import { Message, Document } from '../App';
import { MessageBubble } from './MessageBubble';
import { DocumentSelector } from './DocumentSelector';

interface AnalysisPageProps {
  messages: Message[];
  onSendMessage: (
    query: string,
    analysisType: 'document_search' | 'investment_analysis',
    selectedDocIds?: string[]
  ) => Promise<void>;
  isLoading: boolean;
  documents: Document[];
}

export function AnalysisPage({
  messages,
  onSendMessage,
  isLoading,
  documents
}: AnalysisPageProps) {
  const [input, setInput] = useState('');
  const [analysisType, setAnalysisType] = useState<'document_search' | 'investment_analysis'>('investment_analysis');
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [showDocSelector, setShowDocSelector] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    // For document search, require at least one document selected
    if (analysisType === 'document_search' && selectedDocIds.length === 0) {
      alert('Please select at least one document for search mode');
      return;
    }

    const query = input.trim();
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    
    await onSendMessage(
      query,
      analysisType,
      analysisType === 'document_search' ? selectedDocIds : undefined
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const exampleQueries = analysisType === 'investment_analysis' ? [
    "Should I invest in this FinTech opportunity based on my historical investment patterns?",
    "What types of deals have I historically passed on and why?",
    "Compare this current opportunity against my most successful investments",
    "What are the common characteristics of my best-performing portfolio companies?"
  ] : [
    "What was the EBITDA margin in Q4 2024?",
    "Summarize the key risks identified in the due diligence report",
    "What are the revenue growth rates over the past 3 quarters?",
    "Extract the cap table from the investment memo"
  ];

  return (
    <div className="flex h-full">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-gray-900">Investment Analysis</h2>
              <p className="text-sm text-gray-500 mt-1">
                Ask questions and get insights powered by your document knowledge base
              </p>
            </div>
            
            {/* Analysis Type Toggle */}
            <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setAnalysisType('investment_analysis')}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-md transition-all text-sm
                  ${analysisType === 'investment_analysis'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                  }
                `}
              >
                <Brain size={16} />
                Investment Analysis
              </button>
              <button
                onClick={() => setAnalysisType('document_search')}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-md transition-all text-sm
                  ${analysisType === 'document_search'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                  }
                `}
              >
                <Search size={16} />
                Document Search
              </button>
            </div>
          </div>

          {/* Mode Description */}
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <Sparkles size={16} className="text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-900">
                {analysisType === 'investment_analysis' ? (
                  <>
                    <strong>Investment Analysis Mode:</strong> The AI analyzes your historical investment decisions, identifies patterns in your thesis, and provides recommendations for new opportunities based on your past behavior.
                  </>
                ) : (
                  <>
                    <strong>Document Search Mode:</strong> Search and extract specific information from selected documents. Perfect for finding metrics, tables, and detailed data points.
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 py-6 bg-gray-50">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-2xl">
                <div className="text-5xl mb-4">
                  {analysisType === 'investment_analysis' ? '🎯' : '🔍'}
                </div>
                <h3 className="text-gray-900 mb-2">
                  {analysisType === 'investment_analysis' 
                    ? 'AI-Powered Investment Intelligence'
                    : 'Search Your Documents'
                  }
                </h3>
                <p className="text-sm text-gray-600 mb-6">
                  {analysisType === 'investment_analysis'
                    ? 'Get insights based on your historical investment patterns and decision-making criteria'
                    : 'Find specific information, metrics, and data across your document library'
                  }
                </p>
                
                <div className="bg-white border border-gray-200 rounded-lg p-4 text-left">
                  <p className="text-sm text-gray-700 mb-3">
                    Example queries:
                  </p>
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

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white px-6 py-4">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            {/* Document selector for search mode */}
            {analysisType === 'document_search' && (
              <div className="mb-3">
                <button
                  type="button"
                  onClick={() => setShowDocSelector(!showDocSelector)}
                  className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                >
                  {selectedDocIds.length > 0 
                    ? `${selectedDocIds.length} document${selectedDocIds.length > 1 ? 's' : ''} selected`
                    : 'Select documents to search'
                  }
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
                  onKeyDown={handleKeyDown}
                  placeholder={
                    analysisType === 'investment_analysis'
                      ? "Ask about investment patterns, deal evaluation, or portfolio insights..."
                      : selectedDocIds.length > 0
                        ? "Search selected documents..."
                        : "Select documents first..."
                  }
                  disabled={isLoading || (analysisType === 'document_search' && selectedDocIds.length === 0)}
                  rows={1}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400 resize-none max-h-32"
                />
              </div>
              <button
                type="submit"
                disabled={!input.trim() || isLoading || (analysisType === 'document_search' && selectedDocIds.length === 0)}
                className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {isLoading ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : (
                  <Send size={20} />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Press Enter to send, Shift + Enter for new line
            </p>
          </form>
        </div>
      </div>

      {/* Document Selector Sidebar (for search mode) */}
      {analysisType === 'document_search' && showDocSelector && (
        <DocumentSelector
          documents={documents}
          selectedDocIds={selectedDocIds}
          onToggle={(docId) => {
            setSelectedDocIds(prev =>
              prev.includes(docId)
                ? prev.filter(id => id !== docId)
                : [...prev, docId]
            );
          }}
          onSelectAll={() => {
            if (selectedDocIds.length === documents.length) {
              setSelectedDocIds([]);
            } else {
              setSelectedDocIds(documents.map(d => d.id));
            }
          }}
          onClose={() => setShowDocSelector(false)}
        />
      )}
    </div>
  );
}
