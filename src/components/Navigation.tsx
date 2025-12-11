import React from 'react';
import { Upload, MessageSquare, FolderOpen, TrendingUp } from 'lucide-react';
import { Page, Document } from '../App';

interface NavigationProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
  documents: Document[];
}

export function Navigation({ currentPage, onNavigate, documents }: NavigationProps) {
  const historicalDeals = documents.filter(d => d.category === 'historical_deal').length;
  const currentOpportunities = documents.filter(d => d.category === 'current_opportunity').length;

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp size={24} className="text-blue-400" />
          <h1 className="text-white">PE Analyst AI</h1>
        </div>
        <p className="text-sm text-gray-400">
          Investment Intelligence Platform
        </p>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 p-4">
        <div className="space-y-1">
          <NavItem
            icon={MessageSquare}
            label="Analysis & Query"
            isActive={currentPage === 'analysis'}
            onClick={() => onNavigate('analysis')}
          />
          <NavItem
            icon={Upload}
            label="Upload Documents"
            isActive={currentPage === 'upload'}
            onClick={() => onNavigate('upload')}
          />
          <NavItem
            icon={FolderOpen}
            label="Document Library"
            isActive={currentPage === 'documents'}
            onClick={() => onNavigate('documents')}
            badge={documents.length}
          />
        </div>

        {/* Stats */}
        <div className="mt-8 pt-6 border-t border-gray-800">
          <p className="text-xs text-gray-500 mb-3">DOCUMENT STATS</p>
          <div className="space-y-2">
            <StatItem label="Historical Deals" value={historicalDeals} />
            <StatItem label="Current Opportunities" value={currentOpportunities} />
            <StatItem label="Total Documents" value={documents.length} />
          </div>
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        <div className="bg-gray-800 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">System Status</p>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-300">LLM Connected</span>
          </div>
        </div>
      </div>
    </div>
  );
}

interface NavItemProps {
  icon: React.ElementType;
  label: string;
  isActive: boolean;
  onClick: () => void;
  badge?: number;
}

function NavItem({ icon: Icon, label, isActive, onClick, badge }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors
        ${isActive 
          ? 'bg-blue-600 text-white' 
          : 'text-gray-300 hover:bg-gray-800 hover:text-white'
        }
      `}
    >
      <Icon size={20} />
      <span className="flex-1 text-left text-sm">{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className={`
          px-2 py-0.5 text-xs rounded-full
          ${isActive ? 'bg-blue-700' : 'bg-gray-700'}
        `}>
          {badge}
        </span>
      )}
    </button>
  );
}

interface StatItemProps {
  label: string;
  value: number;
}

function StatItem({ label, value }: StatItemProps) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-gray-400">{label}</span>
      <span className="text-sm text-white">{value}</span>
    </div>
  );
}
