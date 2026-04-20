import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { FileText, Play, Clock, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import type { Deal, WorkflowRun } from '../lib/api';
import { PrecedentCard } from './PrecedentCard';

interface WorkflowPageProps {
  workflowRuns: WorkflowRun[];
  deals: Deal[];
  selectedDocIds: string[];
  latestWorkflow: WorkflowRun | null;
  onRunWorkflow: (query: string, dealId?: string, docIds?: string[]) => void;
  isLoading: boolean;
  onNavigateToDeal?: (dealId: string) => void;
}

export function WorkflowPage({ workflowRuns, deals, selectedDocIds, onRunWorkflow, isLoading, onNavigateToDeal }: WorkflowPageProps) {
  const [query, setQuery] = useState('');
  const [selectedDealId, setSelectedDealId] = useState<string>('');
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);

  const handleLaunch = () => {
    if (!query.trim()) return;
    onRunWorkflow(query, selectedDealId || undefined, selectedDocIds);
    setQuery('');
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Completed</Badge>;
      case 'failed': return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">Failed</Badge>;
      case 'running': return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">Running</Badge>;
      default: return <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-100">Pending</Badge>;
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Launch Trigger Header */}
      <div className="border-b bg-white px-6 py-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">IC Copilot Workflows</h1>
        <p className="text-gray-500 mb-6">Launch rigorous analysis workflows grounded in your document memory.</p>
        
        <div className="flex flex-col gap-4 max-w-4xl">
          <div className="flex gap-4">
            <select
              className="flex-1 max-w-xs rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              value={selectedDealId}
              onChange={(e) => setSelectedDealId(e.target.value)}
            >
              <option value="">No specific deal (General Analysis)</option>
              {deals.map(deal => (
                <option key={deal.id} value={deal.id}>{deal.name}</option>
              ))}
            </select>
            
            <div className="flex-1 flex gap-2">
              <input
                type="text"
                placeholder="e.g., Draft an IC memo outline focusing on go-to-market risks..."
                className="flex-1 rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLaunch()}
                disabled={isLoading}
              />
              <Button onClick={handleLaunch} disabled={isLoading || !query.trim()} className="shrink-0 flex items-center gap-2">
                <Play className="h-4 w-4" />
                Launch Workflow
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
        <div className="max-w-4xl mx-auto space-y-4">
          <h2 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <Clock className="h-5 w-5 text-gray-500" />
            Workflow History
          </h2>
          
          {workflowRuns.length === 0 ? (
            <div className="text-center p-12 border-2 border-dashed border-gray-200 rounded-lg bg-white">
              <p className="text-gray-500">No workflows run yet.</p>
            </div>
          ) : (
            workflowRuns.map((run) => {
              const isExpanded = expandedRunId === run.id;
              const deal = deals.find(d => d.id === run.deal_id);
              
              return (
                <Card key={run.id} className="overflow-hidden bg-white hover:border-gray-300 transition-colors">
                  {/* Collapsed Header */}
                  <div 
                    className="flex items-center justify-between p-4 cursor-pointer"
                    onClick={() => setExpandedRunId(isExpanded ? null : run.id)}
                  >
                    <div className="flex items-center gap-4">
                      {getStatusBadge(run.status)}
                      <div className="flex flex-col">
                        <span className="font-medium text-gray-900">
                          {run.output?.query || 'Workflow Run'}
                        </span>
                        <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                          <span>{new Date(run.created_at).toLocaleString()}</span>
                          {deal && (
                            <>
                              <span>•</span>
                              <span className="font-medium text-blue-600">{deal.name}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="text-gray-400">
                      {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                    </div>
                  </div>

                  {/* Expanded Detail View */}
                  {isExpanded && run.output && (
                    <div className="border-t border-gray-100 p-6 bg-gray-50/50 space-y-8">
                      {/* 1. Precedent Scan (if any) */}
                      {run.output.precedent_scan && run.output.precedent_scan.total > 0 && (
                        <div>
                          <h3 className="text-sm font-bold tracking-wide text-gray-900 uppercase mb-4 flex items-center gap-2">
                            Similar Past Deals ({run.output.precedent_scan.total})
                          </h3>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.values(run.output.precedent_scan.buckets).flat().slice(0, 4).map((record, i) => (
                              <PrecedentCard key={`${run.id}-prec-${i}`} precedent={record} onViewDealDocs={onNavigateToDeal} />
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 2. Synthesis & Draft Answer */}
                      {run.output.draft_answer && (
                        <div>
                          <h3 className="text-sm font-bold tracking-wide text-gray-900 uppercase mb-3">
                            Analysis Synthesis
                          </h3>
                          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                            {run.output.draft_answer}
                          </div>
                        </div>
                      )}

                      {/* 3. Risk Gaps */}
                      {run.output.risk_gaps && run.output.risk_gaps.length > 0 && (
                        <div>
                          <h3 className="text-sm font-bold tracking-wide text-red-900 uppercase mb-3 flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4 text-red-600" />
                            Identified Risk Gaps
                          </h3>
                          <ul className="list-disc pl-5 space-y-2 text-sm text-red-800 bg-red-50 p-4 rounded-lg border border-red-100">
                            {run.output.risk_gaps.map((gap, i) => (
                              <li key={i}>{gap}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Action Footer */}
                      <div className="flex justify-end pt-4 border-t border-gray-200">
                        <Button variant="outline" className="flex items-center gap-2">
                          <FileText className="h-4 w-4" />
                          View Full IC Memo Draft
                        </Button>
                      </div>
                    </div>
                  )}
                </Card>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
