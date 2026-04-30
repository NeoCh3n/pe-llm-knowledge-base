import React, { useEffect, useState } from 'react';
import { Navigation } from './components/Navigation';
import { UploadPage } from './components/UploadPage';
import { AnalysisPage } from './components/AnalysisPage';
import { DocumentsPage } from './components/DocumentsPage';
import { DealsPage } from './components/DealsPage';
import { WorkflowPage } from './components/WorkflowPage';
import { SettingsPage } from './components/SettingsPage';
import { ErrorBoundary } from './components/ErrorBoundary';
import { MobileResponsiveNotice } from './components/MobileResponsiveNotice';
import {
  createDeal,
  deleteDocument,
  fetchDeals,
  fetchDocuments,
  fetchWorkflowRuns,
  postChat,
  runWorkflow,
  uploadDocument,
  type ChatResponse,
  type Deal,
  type DocumentRecord,
  type SourceRecord,
  type WorkflowRun,
} from './lib/api';

export type Document = DocumentRecord;
export type Source = SourceRecord;
export type { Deal, WorkflowRun };
export type Page = 'upload' | 'analysis' | 'documents' | 'deals' | 'workflow' | 'settings';

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: string;
  analysisType?: 'document_search' | 'investment_analysis';
  meta?: {
    modelName?: string;
    promptVersion?: string;
  };
}

interface UploadPayload {
  file: File;
  tags: string[];
  category: Document['category'];
  deal_outcome?: Document['deal_outcome'];
  deal_id?: string;
  document_type?: string;
  language?: string;
}

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('analysis');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [workflowRuns, setWorkflowRuns] = useState<WorkflowRun[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedDealIdFilter, setSelectedDealIdFilter] = useState<string | null>(null);

  useEffect(() => {
    void refreshAll();
  }, []);

  const refreshAll = async () => {
    setErrorMessage(null);
    try {
      const [documentData, dealData, workflowData] = await Promise.all([
        fetchDocuments(),
        fetchDeals(),
        fetchWorkflowRuns(),
      ]);
      setDocuments(documentData);
      setDeals(dealData);
      setWorkflowRuns(workflowData);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to load data.');
    }
  };

  const handleUploadDocuments = async (files: UploadPayload[]) => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      let successCount = 0;
      for (const fileData of files) {
        const formData = new FormData();
        formData.append('file', fileData.file);
        formData.append('tags', JSON.stringify(fileData.tags));
        formData.append('category', fileData.category);
        if (fileData.deal_outcome) {
          formData.append('deal_outcome', fileData.deal_outcome);
        }
        if (fileData.deal_id) {
          formData.append('deal_id', fileData.deal_id);
        }
        if (fileData.document_type) {
          formData.append('document_type', fileData.document_type);
        }
        if (fileData.language) {
          formData.append('language', fileData.language);
        }
        try {
          await uploadDocument(formData);
          successCount++;
        } catch (fileError) {
          console.error('Failed to upload file:', fileData.file.name, fileError);
        }
      }

      if (successCount > 0) {
        await refreshAll();
        setCurrentPage('documents');
        if (successCount < files.length) {
          setErrorMessage(`${successCount} of ${files.length} files uploaded successfully.`);
        }
      } else {
        setErrorMessage('All uploads failed. Please check file types and try again.');
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Upload failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateDeal = async (payload: {
    name: string;
    company_name?: string;
    sector?: string;
    geography?: string;
    stage?: string;
    fund_name?: string;
    vintage_year?: number;
    strategy?: string;
    decision_status?: string;
    outcome_status?: string;
    partner_owner?: string;
    summary?: string;
  }) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const deal = await createDeal(payload);
      if (deal) {
        setDeals((prev) => [deal, ...prev.filter((item) => item.id !== deal.id)]);
      }
      setCurrentPage('deals');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Deal creation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    setErrorMessage(null);
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((doc) => doc.id !== docId));
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Delete failed.');
    }
  };

  const handleDeleteBatch = async (docIds: string[]) => {
    setErrorMessage(null);
    try {
      for (const docId of docIds) {
        await deleteDocument(docId);
      }
      setDocuments((prev) => prev.filter((doc) => !docIds.includes(doc.id)));
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Batch delete failed.');
    }
  };

  const handleSendMessage = async (
    query: string,
    analysisType: 'document_search' | 'investment_analysis',
    selectedDocIds?: string[]
  ) => {
    const userMessage: Message = {
      id: `${Date.now()}`,
      type: 'user',
      content: query,
      timestamp: new Date().toISOString(),
      analysisType,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const payload = {
        query,
        doc_ids: selectedDocIds,
        analysis_mode: analysisType,
        filters:
          analysisType === 'investment_analysis'
            ? { categories: ['historical_deal'] }
            : undefined,
      };
      const data = (await postChat(payload)) as ChatResponse;

      // Handle empty answer from LLM
      const answerContent = data.answer?.trim() || 'No response generated from LLM. Please check your LLM configuration.';

      const assistantMessage: Message = {
        id: `${Date.now()}-assistant`,
        type: 'assistant',
        content: answerContent,
        sources: data.sources,
        timestamp: new Date().toISOString(),
        analysisType,
        meta: {
          modelName: data.model_name,
          promptVersion: data.prompt_version,
        },
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const assistantMessage: Message = {
        id: `${Date.now()}-assistant`,
        type: 'assistant',
        content: error instanceof Error ? error.message : 'There was an error processing your request.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setErrorMessage(error instanceof Error ? error.message : 'Chat failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunWorkflow = async (payload: { query: string; doc_ids?: string[]; deal_id?: string }) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const run = await runWorkflow({ ...payload, workflow_type: 'ic_workflow' });
      if (run) {
        setWorkflowRuns((prev) => [run, ...prev]);
        setCurrentPage('workflow');
      } else {
        setErrorMessage('Workflow API is not available yet on the backend.');
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Workflow run failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNavigateToDeal = (dealId: string) => {
    setSelectedDealIdFilter(dealId);
    setCurrentPage('documents');
  };

  const handleNavigate = (page: Page) => {
    setCurrentPage(page);
    if (page !== 'documents') {
      setSelectedDealIdFilter(null);
    }
  };

  return (
    <>
      <MobileResponsiveNotice />
      <div className="flex h-screen bg-gray-50">
      <Navigation
        currentPage={currentPage}
        onNavigate={handleNavigate}
        documents={documents}
        deals={deals}
        workflowRuns={workflowRuns}
      />

      <div className="flex-1 overflow-hidden">
        {errorMessage && (
          <div className="mx-6 mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        {currentPage === 'upload' && (
          <UploadPage onUpload={handleUploadDocuments} onCreateDeal={handleCreateDeal} deals={deals} isLoading={isLoading} />
        )}

        {currentPage === 'analysis' && (
          <AnalysisPage
            messages={messages}
            onSendMessage={handleSendMessage}
            onRunWorkflow={handleRunWorkflow}
            isLoading={isLoading}
            documents={documents}
            deals={deals}
          />
        )}

        {currentPage === 'documents' && (
          <DocumentsPage
            documents={documents}
            deals={deals}
            onDelete={handleDeleteDocument}
            onDeleteBatch={handleDeleteBatch}
            onRefresh={refreshAll}
            dealIdFilter={selectedDealIdFilter}
            onClearDealFilter={() => setSelectedDealIdFilter(null)}
          />
        )}

        {currentPage === 'deals' && <DealsPage deals={deals} onCreateDeal={handleCreateDeal} isLoading={isLoading} />}

        {currentPage === 'workflow' && (
          <ErrorBoundary>
            <WorkflowPage
              workflowRuns={workflowRuns}
              deals={deals}
              selectedDocIds={[]}
              latestWorkflow={workflowRuns[0] ?? null}
              onRunWorkflow={(query, dealId, docIds) => handleRunWorkflow({ query, deal_id: dealId, doc_ids: docIds })}
              isLoading={isLoading}
              onNavigateToDeal={handleNavigateToDeal}
            />
          </ErrorBoundary>
        )}

        {currentPage === 'settings' && <SettingsPage />}
      </div>
      </div>
    </>
  );
}

export default App;
