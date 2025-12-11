import React, { useState } from 'react';
import { User, Bot, ChevronDown, ChevronUp, FileText, Brain, Search } from 'lucide-react';
import { Message } from '../App';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.type === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
          {message.analysisType === 'investment_analysis' ? (
            <Brain size={18} className="text-blue-600" />
          ) : (
            <Bot size={18} className="text-blue-600" />
          )}
        </div>
      )}
      
      <div className={`flex-1 max-w-3xl ${isUser ? 'flex justify-end' : ''}`}>
        <div className={`
          rounded-lg px-4 py-3 
          ${isUser 
            ? 'bg-blue-600 text-white' 
            : 'bg-white border border-gray-200'
          }
        `}>
          {/* Analysis Type Badge for user messages */}
          {isUser && message.analysisType && (
            <div className="flex items-center gap-1 mb-2 text-xs text-blue-100">
              {message.analysisType === 'investment_analysis' ? (
                <>
                  <Brain size={12} />
                  <span>Investment Analysis</span>
                </>
              ) : (
                <>
                  <Search size={12} />
                  <span>Document Search</span>
                </>
              )}
            </div>
          )}
          
          <div className={`whitespace-pre-wrap ${isUser ? 'text-white' : 'text-gray-900'}`}>
            {message.content}
          </div>
          
          {!isUser && message.sources && message.sources.length > 0 && (
            <SourceCitations sources={message.sources} />
          )}
        </div>
        
        <div className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : ''}`}>
          {new Date(message.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
          <User size={18} className="text-gray-600" />
        </div>
      )}
    </div>
  );
}

interface SourceCitationsProps {
  sources: Message['sources'];
}

function SourceCitations({ sources }: SourceCitationsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-4 border-t border-gray-200 pt-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 transition-colors w-full"
      >
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        <span>
          {sources.length} Source{sources.length > 1 ? 's' : ''} Referenced
        </span>
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-3">
          {sources.map((source, index) => (
            <div
              key={index}
              className="bg-gray-50 rounded-lg p-3 border border-gray-200"
            >
              <div className="flex items-start gap-2 mb-2">
                <FileText size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 break-words">
                    {source.filename}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <p className="text-xs text-gray-500">
                      Page {source.page_number}
                    </p>
                    {source.category && (
                      <span className="text-xs text-gray-400">
                        • {source.category.replace('_', ' ')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded p-2 border border-gray-200">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono overflow-x-auto">
                  {source.chunk_text}
                </pre>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}