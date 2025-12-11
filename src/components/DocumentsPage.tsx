import React, { useState } from 'react';
import { FileText, Trash2, RefreshCw, Filter, Calendar, Tag } from 'lucide-react';
import { Document } from '../App';

interface DocumentsPageProps {
  documents: Document[];
  onDelete: (docId: string) => Promise<void>;
  onRefresh: () => Promise<void>;
}

export function DocumentsPage({ documents, onDelete, onRefresh }: DocumentsPageProps) {
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredDocuments = documents.filter(doc => {
    const matchesCategory = filterCategory === 'all' || doc.category === filterCategory;
    const matchesSearch = searchQuery === '' || 
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const categoryStats = {
    all: documents.length,
    historical_deal: documents.filter(d => d.category === 'historical_deal').length,
    current_opportunity: documents.filter(d => d.category === 'current_opportunity').length,
    market_research: documents.filter(d => d.category === 'market_research').length,
    portfolio_report: documents.filter(d => d.category === 'portfolio_report').length,
    other: documents.filter(d => d.category === 'other').length
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-7xl mx-auto p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-gray-900 mb-2">Document Library</h1>
            <p className="text-gray-600">
              Manage and organize your investment documents
            </p>
          </div>
          <button
            onClick={onRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw size={18} />
            Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by filename or tags..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <Filter className="absolute left-3 top-2.5 text-gray-400" size={18} />
              </div>
            </div>
            
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Categories ({categoryStats.all})</option>
              <option value="historical_deal">Historical Deals ({categoryStats.historical_deal})</option>
              <option value="current_opportunity">Current Opportunities ({categoryStats.current_opportunity})</option>
              <option value="market_research">Market Research ({categoryStats.market_research})</option>
              <option value="portfolio_report">Portfolio Reports ({categoryStats.portfolio_report})</option>
              <option value="other">Other ({categoryStats.other})</option>
            </select>
          </div>
        </div>

        {/* Documents Grid */}
        {filteredDocuments.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <FileText className="mx-auto mb-4 text-gray-300" size={48} />
            <h3 className="text-gray-900 mb-2">
              {searchQuery || filterCategory !== 'all' ? 'No documents found' : 'No documents yet'}
            </h3>
            <p className="text-sm text-gray-500">
              {searchQuery || filterCategory !== 'all' 
                ? 'Try adjusting your filters'
                : 'Upload documents to get started'
              }
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredDocuments.map(doc => (
              <DocumentCard
                key={doc.id}
                document={doc}
                onDelete={onDelete}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface DocumentCardProps {
  document: Document;
  onDelete: (docId: string) => Promise<void>;
}

function DocumentCard({ document, onDelete }: DocumentCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete "${document.filename}"?`)) {
      return;
    }

    setIsDeleting(true);
    try {
      await onDelete(document.id);
    } catch (error) {
      console.error('Error deleting document:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const categoryColors = {
    historical_deal: 'bg-purple-100 text-purple-700',
    current_opportunity: 'bg-green-100 text-green-700',
    market_research: 'bg-blue-100 text-blue-700',
    portfolio_report: 'bg-orange-100 text-orange-700',
    other: 'bg-gray-100 text-gray-700'
  };

  const categoryLabels = {
    historical_deal: 'Historical Deal',
    current_opportunity: 'Current Opportunity',
    market_research: 'Market Research',
    portfolio_report: 'Portfolio Report',
    other: 'Other'
  };

  const outcomeLabels = {
    invested: '✓ Invested',
    passed: '✗ Passed',
    exited: '↗ Exited'
  };

  const outcomeColors = {
    invested: 'bg-green-100 text-green-700',
    passed: 'bg-red-100 text-red-700',
    exited: 'bg-blue-100 text-blue-700'
  };

  const uploadDate = new Date(document.upload_timestamp);
  const formattedDate = uploadDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <FileText className="text-blue-600" size={24} />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-2">
            <h3 className="text-gray-900 break-words">
              {document.filename}
            </h3>
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="flex-shrink-0 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            >
              <Trash2 size={18} />
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3 mb-3">
            <div className="flex items-center gap-1.5 text-sm text-gray-500">
              <Calendar size={14} />
              {formattedDate}
            </div>
            
            <span className={`px-2.5 py-1 text-xs rounded ${categoryColors[document.category]}`}>
              {categoryLabels[document.category]}
            </span>

            {document.deal_outcome && (
              <span className={`px-2.5 py-1 text-xs rounded ${outcomeColors[document.deal_outcome]}`}>
                {outcomeLabels[document.deal_outcome]}
              </span>
            )}
          </div>

          {document.tags.length > 0 && (
            <div className="flex items-center gap-2">
              <Tag size={14} className="text-gray-400" />
              <div className="flex flex-wrap gap-2">
                {document.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
