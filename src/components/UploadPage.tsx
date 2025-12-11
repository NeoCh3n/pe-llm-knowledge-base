import React, { useState } from 'react';
import { Upload, X, Plus, FileText, Check } from 'lucide-react';
import { Document } from '../App';

interface UploadPageProps {
  onUpload: (files: Array<{
    file: File;
    tags: string[];
    category: Document['category'];
    deal_outcome?: Document['deal_outcome'];
  }>) => Promise<void>;
  isLoading: boolean;
}

interface PendingFile {
  id: string;
  file: File;
  tags: string[];
  category: Document['category'];
  deal_outcome?: Document['deal_outcome'];
}

export function UploadPage({ onUpload, isLoading }: UploadPageProps) {
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf' || 
              file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    );

    addFiles(files);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      addFiles(files);
      e.target.value = ''; // Reset input
    }
  };

  const addFiles = (files: File[]) => {
    const newPendingFiles: PendingFile[] = files.map(file => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      tags: [],
      category: 'other'
    }));
    setPendingFiles(prev => [...prev, ...newPendingFiles]);
  };

  const removeFile = (id: string) => {
    setPendingFiles(prev => prev.filter(f => f.id !== id));
  };

  const updateFile = (id: string, updates: Partial<PendingFile>) => {
    setPendingFiles(prev => prev.map(f => 
      f.id === id ? { ...f, ...updates } : f
    ));
  };

  const handleUploadAll = async () => {
    if (pendingFiles.length === 0) return;

    const filesToUpload = pendingFiles.map(pf => ({
      file: pf.file,
      tags: pf.tags,
      category: pf.category,
      deal_outcome: pf.deal_outcome
    }));

    await onUpload(filesToUpload);
    setPendingFiles([]);
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-6xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-gray-900 mb-2">Upload Documents</h1>
          <p className="text-gray-600">
            Upload deal memos, due diligence reports, market research, and portfolio documents to build your investment knowledge base
          </p>
        </div>

        {/* Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-xl p-12 text-center transition-all mb-8
            ${isDragging 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 bg-white hover:border-gray-400'
            }
          `}
        >
          <Upload className="mx-auto mb-4 text-gray-400" size={48} />
          <h3 className="text-gray-900 mb-2">
            Drop files here or click to browse
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Supports PDF and DOCX files (Multiple files allowed)
          </p>
          <input
            type="file"
            multiple
            accept=".pdf,.docx"
            onChange={handleFileSelect}
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

        {/* Pending Files */}
        {pendingFiles.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div>
                <h3 className="text-gray-900">
                  Pending Uploads ({pendingFiles.length})
                </h3>
                <p className="text-sm text-gray-500 mt-0.5">
                  Configure document details before uploading
                </p>
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
              {pendingFiles.map(pendingFile => (
                <FileConfigRow
                  key={pendingFile.id}
                  pendingFile={pendingFile}
                  onUpdate={(updates) => updateFile(pendingFile.id, updates)}
                  onRemove={() => removeFile(pendingFile.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Upload Tips */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h4 className="text-blue-900 mb-3">
            📚 Document Organization Tips
          </h4>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>
              <strong>Historical Deals:</strong> Past investment memos, DD reports, and deal outcomes. Mark whether you invested or passed to build pattern recognition.
            </li>
            <li>
              <strong>Current Opportunities:</strong> Active deals under evaluation. The AI will compare these against your historical investment criteria.
            </li>
            <li>
              <strong>Market Research:</strong> Industry reports, market sizing, competitive analysis to provide context.
            </li>
            <li>
              <strong>Portfolio Reports:</strong> Performance tracking, board decks, financial statements from existing investments.
            </li>
            <li>
              <strong>Tags:</strong> Use consistent tags (e.g., "SaaS", "Series B", "Healthcare") to help the AI identify patterns in your investment thesis.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

interface FileConfigRowProps {
  pendingFile: PendingFile;
  onUpdate: (updates: Partial<PendingFile>) => void;
  onRemove: () => void;
}

function FileConfigRow({ pendingFile, onUpdate, onRemove }: FileConfigRowProps) {
  const [tagInput, setTagInput] = useState('');

  const handleAddTag = () => {
    if (tagInput.trim()) {
      onUpdate({ tags: [...pendingFile.tags, tagInput.trim()] });
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onUpdate({ tags: pendingFile.tags.filter(t => t !== tagToRemove) });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex gap-6">
        {/* File Info */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <FileText className="text-blue-600" size={24} />
          </div>
        </div>

        {/* Configuration */}
        <div className="flex-1 min-w-0 space-y-4">
          <div>
            <p className="text-gray-900 truncate">
              {pendingFile.file.name}
            </p>
            <p className="text-sm text-gray-500">
              {(pendingFile.file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Category */}
            <div>
              <label className="block text-sm text-gray-700 mb-1.5">
                Document Category *
              </label>
              <select
                value={pendingFile.category}
                onChange={(e) => onUpdate({ category: e.target.value as Document['category'] })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="other">General Document</option>
                <option value="historical_deal">Historical Deal</option>
                <option value="current_opportunity">Current Opportunity</option>
                <option value="market_research">Market Research</option>
                <option value="portfolio_report">Portfolio Report</option>
              </select>
            </div>

            {/* Deal Outcome (conditional) */}
            {pendingFile.category === 'historical_deal' && (
              <div>
                <label className="block text-sm text-gray-700 mb-1.5">
                  Deal Outcome *
                </label>
                <select
                  value={pendingFile.deal_outcome || ''}
                  onChange={(e) => onUpdate({ deal_outcome: e.target.value as Document['deal_outcome'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                >
                  <option value="">Select outcome...</option>
                  <option value="invested">Invested</option>
                  <option value="passed">Passed</option>
                  <option value="exited">Exited</option>
                </select>
              </div>
            )}
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm text-gray-700 mb-1.5">
              Tags (e.g., SaaS, Series B, Healthcare)
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Add a tag..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
              <button
                onClick={handleAddTag}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
              >
                <Plus size={16} />
              </button>
            </div>
            {pendingFile.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {pendingFile.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-100 text-blue-700 rounded text-sm"
                  >
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="hover:text-blue-900"
                    >
                      <X size={14} />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Remove Button */}
        <div className="flex-shrink-0">
          <button
            onClick={onRemove}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
