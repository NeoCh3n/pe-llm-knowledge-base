import React, { useMemo, useState } from 'react';
import { FileText, Trash2, RefreshCw, Filter, Calendar, Tag } from 'lucide-react';
import { Document } from '../App';
import type { Deal } from '../lib/api';

interface DocumentsPageProps {
  documents: Document[];
  deals: Deal[];
  onDelete: (docId: string) => Promise<void>;
  onRefresh: () => Promise<void>;
}

export function DocumentsPage({ documents, deals, onDelete, onRefresh }: DocumentsPageProps) {
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredDocuments = useMemo(
    () =>
      documents.filter((doc) => {
        const matchesCategory = filterCategory === 'all' || doc.category === filterCategory;
        const matchesSearch =
          searchQuery === '' ||
          doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
          doc.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()));
        return matchesCategory && matchesSearch;
      }),
    [documents, filterCategory, searchQuery]
  );

  const categoryStats = {
    all: documents.length,
    historical_deal: documents.filter((d) => d.category === 'historical_deal').length,
    current_opportunity: documents.filter((d) => d.category === 'current_opportunity').length,
    market_research: documents.filter((d) => d.category === 'market_research').length,
    portfolio_report: documents.filter((d) => d.category === 'portfolio_report').length,
    other: documents.filter((d) => d.category === 'other').length,
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-7xl mx-auto p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-gray-900 mb-2">Document Library</h1>
            <p className="text-gray-600">Search, filter, and prune the evidence base backing the institutional memory system.</p>
          </div>
          <button onClick={onRefresh} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
            <RefreshCw size={18} />
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr,260px] gap-6 mb-6">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
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

          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="all">All Categories ({categoryStats.all})</option>
              <option value="historical_deal">Historical Deals ({categoryStats.historical_deal})</option>
              <option value="current_opportunity">Current Opportunities ({categoryStats.current_opportunity})</option>
              <option value="market_research">Market Research ({categoryStats.market_research})</option>
              <option value="portfolio_report">Portfolio Reports ({categoryStats.portfolio_report})</option>
              <option value="other">Other ({categoryStats.other})</option>
            </select>
            <div className="mt-4 rounded-lg bg-blue-50 border border-blue-200 p-3">
              <p className="text-xs text-blue-700 uppercase tracking-wide mb-1">Canonical deals</p>
              <p className="text-2xl text-blue-900">{deals.length}</p>
            </div>
          </div>
        </div>

        {filteredDocuments.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <FileText className="mx-auto mb-4 text-gray-300" size={48} />
            <h3 className="text-gray-900 mb-2">{searchQuery || filterCategory !== 'all' ? 'No documents found' : 'No documents yet'}</h3>
            <p className="text-sm text-gray-500">{searchQuery || filterCategory !== 'all' ? 'Try adjusting your filters.' : 'Upload source documents to get started.'}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredDocuments.map((doc) => (
              <DocumentCard key={doc.id} document={doc} onDelete={onDelete} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function DocumentCard({ document, onDelete }: { document: Document; onDelete: (docId: string) => Promise<void> }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const uploadDate = new Date(document.upload_timestamp);
  const categoryColors = {
    historical_deal: 'bg-purple-100 text-purple-700',
    current_opportunity: 'bg-green-100 text-green-700',
    market_research: 'bg-blue-100 text-blue-700',
    portfolio_report: 'bg-orange-100 text-orange-700',
    other: 'bg-gray-100 text-gray-700',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <FileText className="text-blue-600" size={24} />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-2">
            <h3 className="text-gray-900 break-words">{document.filename}</h3>
            <button
              onClick={async () => {
                if (!confirm(`Are you sure you want to delete "${document.filename}"?`)) return;
                setIsDeleting(true);
                try {
                  await onDelete(document.id);
                } finally {
                  setIsDeleting(false);
                }
              }}
              disabled={isDeleting}
              className="flex-shrink-0 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            >
              <Trash2 size={18} />
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3 mb-3">
            <div className="flex items-center gap-1.5 text-sm text-gray-500">
              <Calendar size={14} />
              {uploadDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </div>
            <span className={`px-2.5 py-1 text-xs rounded ${categoryColors[document.category]}`}>{document.category.replace('_', ' ')}</span>
            {document.deal_outcome && <span className="px-2.5 py-1 text-xs rounded bg-gray-100 text-gray-700">{document.deal_outcome}</span>}
          </div>

          {document.tags.length > 0 && (
            <div className="flex items-center gap-2">
              <Tag size={14} className="text-gray-400" />
              <div className="flex flex-wrap gap-2">
                {document.tags.map((tag, index) => (
                  <span key={index} className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded">
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
