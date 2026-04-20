import React from 'react';
import { Card, CardContent, CardHeader } from './ui/card';
import { Badge } from './ui/badge';
import type { PrecedentRecord } from '../lib/api';

interface PrecedentCardProps {
  precedent: PrecedentRecord;
  onViewDealDocs?: (dealId: string) => void;
}

// Convert similarity score float to confidence band
function getConfidenceBand(score: number): { label: string; color: string } {
  if (score > 0.85) return { label: 'High Confidence', color: 'bg-green-100 text-green-800' };
  if (score > 0.75) return { label: 'Medium Confidence', color: 'bg-yellow-100 text-yellow-800' };
  return { label: 'Low Confidence', color: 'bg-gray-100 text-gray-800' };
}

function getDecisionColor(status: string | null | undefined): string {
  if (!status) return 'bg-gray-100 text-gray-800';
  const s = status.toLowerCase();
  if (s.includes('passed') || s.includes('approved')) return 'bg-green-100 text-green-800';
  if (s.includes('reject')) return 'bg-red-100 text-red-800';
  if (s.includes('withdraw')) return 'bg-orange-100 text-orange-800';
  return 'bg-blue-100 text-blue-800'; // pending
}

function getOutcomeColor(status: string | null | undefined): string {
  if (!status) return 'bg-gray-100 text-gray-800';
  const s = status.toLowerCase();
  if (s.includes('realized')) return 'bg-emerald-100 text-emerald-800';
  if (s.includes('written-off')) return 'bg-rose-100 text-rose-800';
  if (s.includes('unrealized')) return 'bg-purple-100 text-purple-800';
  return 'bg-gray-100 text-gray-800'; // pending
}

function getCategoryBorder(category: string): string {
  switch (category) {
    case 'historical_deal':
      return 'border-l-4 border-l-blue-500';
    case 'current_opportunity':
      return 'border-l-4 border-l-emerald-500';
    case 'market_research':
      return 'border-l-4 border-l-purple-500';
    case 'portfolio_report':
      return 'border-l-4 border-l-amber-500';
    default:
      return 'border-l-4 border-l-gray-400';
  }
}

export function PrecedentCard({ precedent, onViewDealDocs }: PrecedentCardProps) {
  const confidence = getConfidenceBand(precedent.score);
  const borderClass = getCategoryBorder(precedent.category);
  const hasDealId = precedent.deal_id && precedent.deal_id !== '';

  return (
    <Card className={`mb-4 overflow-hidden ${borderClass} shadow-sm border-gray-200`}>
      <CardHeader className="bg-gray-50/50 pb-3 top-0">
        <div className="flex items-start justify-between">
          <div className="flex flex-col gap-1">
            <h3 className="font-semibold text-lg text-gray-900 leading-none">
              {precedent.deal_name || 'Unnamed Deal'}
            </h3>
            {(precedent.sector || precedent.geography || precedent.stage) && (
              <span className="text-sm text-gray-500">
                {[precedent.sector, precedent.geography, precedent.stage].filter(Boolean).join(' • ')}
              </span>
            )}
          </div>
          <div className="flex flex-col gap-2 items-end">
            <Badge variant="outline" className={`${confidence.color} border-none font-medium`}>
              {confidence.label}
            </Badge>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-2 mt-3">
          {precedent.decision_status && (
            <Badge variant="secondary" className={`${getDecisionColor(precedent.decision_status)} border-none`}>
              Decision: {precedent.decision_status}
            </Badge>
          )}
          {precedent.outcome_status && (
            <Badge variant="secondary" className={`${getOutcomeColor(precedent.outcome_status)} border-none`}>
              Outcome: {precedent.outcome_status}
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="pt-4">
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-900">Key Evidence</h4>
              <span className="text-xs text-gray-500 font-mono">
                {precedent.filename} • p.{precedent.page_number}
              </span>
            </div>
            {precedent.evidence ? (
              <div className="relative">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-gray-200 rounded"></div>
                <p className="text-sm text-gray-700 leading-relaxed pl-4 pr-2 italic line-clamp-4">
                  "{precedent.evidence}"
                </p>
              </div>
            ) : (
              <p className="text-sm text-gray-500 italic">No direct excerpt available.</p>
            )}
          </div>
          
          <div className="pt-2 flex justify-end">
            {hasDealId && onViewDealDocs ? (
              <button
                onClick={() => onViewDealDocs(precedent.deal_id!)}
                className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline"
              >
                View deal docs →
              </button>
            ) : (
              <span className="text-sm text-gray-400">No linked deal</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
