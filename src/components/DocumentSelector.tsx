import React from 'react';
import { X, CheckSquare, Square, FileText } from 'lucide-react';
import { Document } from '../App';

interface DocumentSelectorProps {
  documents: Document[];
  selectedDocIds: string[];
  onToggle: (docId: string) => void;
  onSelectAll: () => void;
  onClose: () => void;
}

export function DocumentSelector({
  documents,
  selectedDocIds,
  onToggle,
  onSelectAll,
  onClose
}: DocumentSelectorProps) {
  const allSelected = documents.length > 0 && selectedDocIds.length === documents.length;

  const categoryGroups = {
    historical_deal: documents.filter(d => d.category === 'historical_deal'),
    current_opportunity: documents.filter(d => d.category === 'current_opportunity'),
    market_research: documents.filter(d => d.category === 'market_research'),
    portfolio_report: documents.filter(d => d.category === 'portfolio_report'),
    other: documents.filter(d => d.category === 'other')
  };

  const categoryLabels = {
    historical_deal: 'Historical Deals',
    current_opportunity: 'Current Opportunities',
    market_research: 'Market Research',
    portfolio_report: 'Portfolio Reports',
    other: 'Other Documents'
  };

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="text-gray-900">Select Documents</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {selectedDocIds.length} of {documents.length} selected
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 rounded"
        >
          <X size={20} />
        </button>
      </div>

      {/* Actions */}
      <div className="px-4 py-2 border-b border-gray-200">
        <button
          onClick={onSelectAll}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          {allSelected ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {Object.entries(categoryGroups).map(([category, docs]) => {
          if (docs.length === 0) return null;

          return (
            <div key={category}>
              <h4 className="text-xs text-gray-500 mb-2 uppercase tracking-wide">
                {categoryLabels[category as keyof typeof categoryLabels]}
              </h4>
              <div className="space-y-1">
                {docs.map(doc => (
                  <DocumentItem
                    key={doc.id}
                    document={doc}
                    isSelected={selectedDocIds.includes(doc.id)}
                    onToggle={() => onToggle(doc.id)}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface DocumentItemProps {
  document: Document;
  isSelected: boolean;
  onToggle: () => void;
}

function DocumentItem({ document, isSelected, onToggle }: DocumentItemProps) {
  return (
    <div
      onClick={onToggle}
      className={`
        p-2 rounded-lg border cursor-pointer transition-all
        ${isSelected 
          ? 'border-blue-500 bg-blue-50' 
          : 'border-gray-200 bg-white hover:border-gray-300'
        }
      `}
    >
      <div className="flex items-start gap-2">
        <div className="mt-0.5 flex-shrink-0">
          {isSelected ? (
            <CheckSquare size={16} className="text-blue-600" />
          ) : (
            <Square size={16} className="text-gray-400" />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-1.5">
            <FileText size={14} className="text-gray-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-gray-900 break-words leading-tight">
              {document.filename}
            </p>
          </div>
          
          {document.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {document.tags.slice(0, 2).map((tag, index) => (
                <span
                  key={index}
                  className="inline-block px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                >
                  {tag}
                </span>
              ))}
              {document.tags.length > 2 && (
                <span className="text-xs text-gray-400">
                  +{document.tags.length - 2}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
