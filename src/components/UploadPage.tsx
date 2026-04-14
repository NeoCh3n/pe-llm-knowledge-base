import React, { useMemo, useState } from 'react';
import { Upload, X, Plus, FileText, Link2 } from 'lucide-react';
import { Document } from '../App';
import type { Deal } from '../lib/api';

interface UploadPageProps {
  onUpload: (files: Array<{
    file: File;
    tags: string[];
    category: Document['category'];
    deal_outcome?: Document['deal_outcome'];
    deal_id?: string;
    document_type?: string;
    language?: string;
  }>) => Promise<void>;
  onCreateDeal: (payload: {
    name: string;
    company_name?: string;
    sector?: string;
    geography?: string;
    stage?: string;
    fund_name?: string;
    decision_status?: string;
    outcome_status?: string;
    partner_owner?: string;
    summary?: string;
  }) => Promise<void>;
  deals: Deal[];
  isLoading: boolean;
}

interface PendingFile {
  id: string;
  file: File;
  tags: string[];
  category: Document['category'];
  deal_outcome?: Document['deal_outcome'];
  deal_id?: string;
  document_type?: string;
  language?: string;
}

export function UploadPage({ onUpload, onCreateDeal, deals, isLoading }: UploadPageProps) {
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [dealForm, setDealForm] = useState({
    name: '',
    company_name: '',
    sector: '',
    geography: '',
    stage: '',
    fund_name: '',
    decision_status: '',
    outcome_status: '',
    partner_owner: '',
    summary: '',
  });

  const sortedDeals = useMemo(
    () => [...deals].sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1)),
    [deals]
  );

  const addFiles = (files: File[]) => {
    const validFiles = files.filter(
      (file) =>
        file.type === 'application/pdf' ||
        file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
        file.name.endsWith('.pdf') ||
        file.name.endsWith('.docx')
    );

    const newPendingFiles: PendingFile[] = validFiles.map((file) => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      tags: [],
      category: 'other',
      language: 'en',
      document_type: 'memo',
    }));
    setPendingFiles((prev) => [...prev, ...newPendingFiles]);
  };

  const handleUploadAll = async () => {
    if (pendingFiles.length === 0) return;
    await onUpload(
      pendingFiles.map((item) => ({
        file: item.file,
        tags: item.tags,
        category: item.category,
        deal_outcome: item.deal_outcome,
        deal_id: item.deal_id,
        document_type: item.document_type,
        language: item.language,
      }))
    );
    setPendingFiles([]);
  };

  const handleCreateDeal = async () => {
    if (!dealForm.name.trim()) return;
    await onCreateDeal({
      ...dealForm,
      name: dealForm.name.trim(),
      company_name: dealForm.company_name || undefined,
      sector: dealForm.sector || undefined,
      geography: dealForm.geography || undefined,
      stage: dealForm.stage || undefined,
      fund_name: dealForm.fund_name || undefined,
      decision_status: dealForm.decision_status || undefined,
      outcome_status: dealForm.outcome_status || undefined,
      partner_owner: dealForm.partner_owner || undefined,
      summary: dealForm.summary || undefined,
    });
    setDealForm({
      name: '',
      company_name: '',
      sector: '',
      geography: '',
      stage: '',
      fund_name: '',
      decision_status: '',
      outcome_status: '',
      partner_owner: '',
      summary: '',
    });
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-6xl mx-auto p-8 space-y-8">
        <div>
          <h1 className="text-gray-900 mb-2">Upload Evidence</h1>
          <p className="text-gray-600">
            Ingest memos, DD reports, portfolio reviews, and market research into the institutional memory layer.
          </p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[1.4fr,0.9fr] gap-8">
          <div>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setIsDragging(false);
              }}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                addFiles(Array.from(e.dataTransfer.files));
              }}
              className={`
                border-2 border-dashed rounded-xl p-12 text-center transition-all mb-8
                ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-gray-400'}
              `}
            >
              <Upload className="mx-auto mb-4 text-gray-400" size={48} />
              <h3 className="text-gray-900 mb-2">Drop files here or click to browse</h3>
              <p className="text-sm text-gray-500 mb-4">PDF and DOCX only. Each file can be linked to a canonical deal.</p>
              <input
                type="file"
                multiple
                accept=".pdf,.docx"
                onChange={(e) => {
                  if (e.target.files) {
                    addFiles(Array.from(e.target.files));
                    e.target.value = '';
                  }
                }}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors"
              >
                <Plus size={20} />
                Select Files
              </label>
            </div>

            {pendingFiles.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
                  <div>
                    <h3 className="text-gray-900">Pending Uploads ({pendingFiles.length})</h3>
                    <p className="text-sm text-gray-500 mt-0.5">Attach metadata before indexing.</p>
                  </div>
                  <button
                    onClick={handleUploadAll}
                    disabled={isLoading}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Upload size={18} />
                    {isLoading ? 'Uploading...' : `Upload All (${pendingFiles.length})`}
                  </button>
                </div>
                <div className="divide-y divide-gray-200">
                  {pendingFiles.map((pendingFile) => (
                    <FileConfigRow
                      key={pendingFile.id}
                      pendingFile={pendingFile}
                      deals={sortedDeals}
                      onUpdate={(updates) =>
                        setPendingFiles((prev) => prev.map((file) => (file.id === pendingFile.id ? { ...file, ...updates } : file)))
                      }
                      onRemove={() => setPendingFiles((prev) => prev.filter((file) => file.id !== pendingFile.id))}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Link2 size={18} className="text-blue-600" />
                <h3 className="text-gray-900">Create Canonical Deal</h3>
              </div>
              <div className="space-y-3">
                <input
                  value={dealForm.name}
                  onChange={(e) => setDealForm((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="Deal name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
                <div className="grid grid-cols-2 gap-3">
                  <input value={dealForm.company_name} onChange={(e) => setDealForm((prev) => ({ ...prev, company_name: e.target.value }))} placeholder="Company" className="w-full px-3 py-2 border border-gray-300 rounded-lg" />
                  <input value={dealForm.sector} onChange={(e) => setDealForm((prev) => ({ ...prev, sector: e.target.value }))} placeholder="Sector" className="w-full px-3 py-2 border border-gray-300 rounded-lg" />
                  <input value={dealForm.geography} onChange={(e) => setDealForm((prev) => ({ ...prev, geography: e.target.value }))} placeholder="Geography" className="w-full px-3 py-2 border border-gray-300 rounded-lg" />
                  <input value={dealForm.stage} onChange={(e) => setDealForm((prev) => ({ ...prev, stage: e.target.value }))} placeholder="Stage" className="w-full px-3 py-2 border border-gray-300 rounded-lg" />
                  <input value={dealForm.fund_name} onChange={(e) => setDealForm((prev) => ({ ...prev, fund_name: e.target.value }))} placeholder="Fund" className="w-full px-3 py-2 border border-gray-300 rounded-lg" />
                  <input value={dealForm.partner_owner} onChange={(e) => setDealForm((prev) => ({ ...prev, partner_owner: e.target.value }))} placeholder="Partner owner" className="w-full px-3 py-2 border border-gray-300 rounded-lg" />
                </div>
                <textarea value={dealForm.summary} onChange={(e) => setDealForm((prev) => ({ ...prev, summary: e.target.value }))} placeholder="Short summary / thesis" rows={4} className="w-full px-3 py-2 border border-gray-300 rounded-lg" />
                <button
                  onClick={handleCreateDeal}
                  disabled={isLoading || !dealForm.name.trim()}
                  className="w-full px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
                >
                  Create Deal
                </button>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h4 className="text-blue-900 mb-3">Ingestion guidance</h4>
              <ul className="text-sm text-blue-800 space-y-2">
                <li>Link historical documents to a canonical deal whenever possible.</li>
                <li>Use consistent tags for sector, stage, region, and theme.</li>
                <li>Mark historical outcomes so precedent retrieval can separate approved, rejected, and successful cases.</li>
                <li>Keep memo and DD report files separate if you want later workflow steps to cite them independently.</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface FileConfigRowProps {
  pendingFile: PendingFile;
  deals: Deal[];
  onUpdate: (updates: Partial<PendingFile>) => void;
  onRemove: () => void;
}

function FileConfigRow({ pendingFile, deals, onUpdate, onRemove }: FileConfigRowProps) {
  const [tagInput, setTagInput] = useState('');

  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex gap-6">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <FileText className="text-blue-600" size={24} />
          </div>
        </div>

        <div className="flex-1 min-w-0 space-y-4">
          <div>
            <p className="text-gray-900 truncate">{pendingFile.file.name}</p>
            <p className="text-sm text-gray-500">{(pendingFile.file.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <select value={pendingFile.category} onChange={(e) => onUpdate({ category: e.target.value as Document['category'] })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="other">General Document</option>
              <option value="historical_deal">Historical Deal</option>
              <option value="current_opportunity">Current Opportunity</option>
              <option value="market_research">Market Research</option>
              <option value="portfolio_report">Portfolio Report</option>
            </select>
            <select value={pendingFile.document_type || 'memo'} onChange={(e) => onUpdate({ document_type: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="memo">IC Memo</option>
              <option value="dd_report">DD Report</option>
              <option value="board_material">Board Material</option>
              <option value="portfolio_review">Portfolio Review</option>
              <option value="market_research">Market Research</option>
            </select>
            <select value={pendingFile.language || 'en'} onChange={(e) => onUpdate({ language: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="en">English</option>
              <option value="zh">Chinese</option>
              <option value="mixed">Mixed</option>
            </select>
            <select value={pendingFile.deal_id || ''} onChange={(e) => onUpdate({ deal_id: e.target.value || undefined })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">No linked deal</option>
              {deals.map((deal) => (
                <option key={deal.id} value={deal.id}>
                  {deal.name}
                </option>
              ))}
            </select>
          </div>

          {pendingFile.category === 'historical_deal' && (
            <select value={pendingFile.deal_outcome || ''} onChange={(e) => onUpdate({ deal_outcome: (e.target.value || undefined) as Document['deal_outcome'] })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">Select outcome...</option>
              <option value="invested">Invested</option>
              <option value="passed">Passed</option>
              <option value="exited">Exited</option>
            </select>
          )}

          <div>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && tagInput.trim()) {
                    e.preventDefault();
                    onUpdate({ tags: [...pendingFile.tags, tagInput.trim()] });
                    setTagInput('');
                  }
                }}
                placeholder="Add a tag..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
              <button
                onClick={() => {
                  if (tagInput.trim()) {
                    onUpdate({ tags: [...pendingFile.tags, tagInput.trim()] });
                    setTagInput('');
                  }
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
              >
                <Plus size={16} />
              </button>
            </div>
            {pendingFile.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {pendingFile.tags.map((tag, index) => (
                  <span key={index} className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                    {tag}
                    <button onClick={() => onUpdate({ tags: pendingFile.tags.filter((current) => current !== tag) })} className="hover:text-blue-900">
                      <X size={14} />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex-shrink-0">
          <button onClick={onRemove} className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
