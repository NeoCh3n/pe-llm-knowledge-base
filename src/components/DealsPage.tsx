import React, { useState } from 'react';
import { Building2, Plus } from 'lucide-react';
import { Deal } from '../App';

interface DealsPageProps {
  deals: Deal[];
  onCreateDeal: (payload: Omit<Deal, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  isLoading: boolean;
}

export function DealsPage({ deals, onCreateDeal, isLoading }: DealsPageProps) {
  const [form, setForm] = useState({
    name: '',
    company_name: '',
    sector: '',
    geography: '',
    stage: '',
    fund_name: '',
    vintage_year: new Date().getFullYear(),
    strategy: '',
    decision_status: '',
    outcome_status: '',
    partner_owner: '',
    summary: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    await onCreateDeal({
      ...form,
      name: form.name.trim(),
      company_name: form.company_name || null,
      sector: form.sector || null,
      geography: form.geography || null,
      stage: form.stage || null,
      fund_name: form.fund_name || null,
      strategy: form.strategy || null,
      decision_status: form.decision_status || null,
      outcome_status: form.outcome_status || null,
      partner_owner: form.partner_owner || null,
      summary: form.summary || null
    });
    setForm({
      name: '',
      company_name: '',
      sector: '',
      geography: '',
      stage: '',
      fund_name: '',
      vintage_year: new Date().getFullYear(),
      strategy: '',
      decision_status: '',
      outcome_status: '',
      partner_owner: '',
      summary: ''
    });
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-7xl mx-auto p-8 space-y-6">
        <div>
          <h1 className="text-gray-900 mb-2">Canonical Deals</h1>
          <p className="text-gray-600">
            Create deal shells to anchor documents, workflows, and outcome history.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Plus size={18} className="text-blue-600" />
            <h2 className="text-gray-900">New Deal</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input value={form.name} onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))} placeholder="Deal name" className="px-3 py-2 border border-gray-300 rounded-lg" />
            <input value={form.company_name} onChange={(e) => setForm(prev => ({ ...prev, company_name: e.target.value }))} placeholder="Company" className="px-3 py-2 border border-gray-300 rounded-lg" />
            <input value={form.sector} onChange={(e) => setForm(prev => ({ ...prev, sector: e.target.value }))} placeholder="Sector" className="px-3 py-2 border border-gray-300 rounded-lg" />
            <input value={form.geography} onChange={(e) => setForm(prev => ({ ...prev, geography: e.target.value }))} placeholder="Geography" className="px-3 py-2 border border-gray-300 rounded-lg" />
            <input value={form.stage} onChange={(e) => setForm(prev => ({ ...prev, stage: e.target.value }))} placeholder="Stage" className="px-3 py-2 border border-gray-300 rounded-lg" />
            <input value={form.fund_name} onChange={(e) => setForm(prev => ({ ...prev, fund_name: e.target.value }))} placeholder="Fund" className="px-3 py-2 border border-gray-300 rounded-lg" />
            <input value={form.strategy} onChange={(e) => setForm(prev => ({ ...prev, strategy: e.target.value }))} placeholder="Strategy" className="px-3 py-2 border border-gray-300 rounded-lg" />
            <input value={form.decision_status} onChange={(e) => setForm(prev => ({ ...prev, decision_status: e.target.value }))} placeholder="Decision status" className="px-3 py-2 border border-gray-300 rounded-lg" />
            <input value={form.outcome_status} onChange={(e) => setForm(prev => ({ ...prev, outcome_status: e.target.value }))} placeholder="Outcome status" className="px-3 py-2 border border-gray-300 rounded-lg" />
            <input value={form.partner_owner} onChange={(e) => setForm(prev => ({ ...prev, partner_owner: e.target.value }))} placeholder="Partner owner" className="px-3 py-2 border border-gray-300 rounded-lg" />
            <input type="number" value={form.vintage_year} onChange={(e) => setForm(prev => ({ ...prev, vintage_year: Number(e.target.value) }))} placeholder="Vintage year" className="px-3 py-2 border border-gray-300 rounded-lg" />
          </div>
          <textarea value={form.summary} onChange={(e) => setForm(prev => ({ ...prev, summary: e.target.value }))} placeholder="Summary" className="w-full px-3 py-2 border border-gray-300 rounded-lg min-h-24" />
          <button type="submit" disabled={isLoading || !form.name.trim()} className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50">
            {isLoading ? 'Saving...' : 'Create Deal'}
          </button>
        </form>

        <div className="grid grid-cols-1 gap-4">
          {deals.map((deal) => (
            <div key={deal.id} className="bg-white border border-gray-200 rounded-xl p-5">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Building2 size={20} className="text-blue-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-gray-900">{deal.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {[deal.company_name, deal.sector, deal.stage, deal.geography].filter(Boolean).join(' • ') || 'No metadata yet'}
                  </p>
                  {deal.summary && (
                    <p className="text-sm text-gray-700 mt-3">{deal.summary}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
          {deals.length === 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-10 text-center text-gray-500">
              No deals yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
