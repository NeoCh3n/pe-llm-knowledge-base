import React, { useState, useEffect } from 'react';
import { Navigation } from './components/Navigation';
import { UploadPage } from './components/UploadPage';
import { AnalysisPage } from './components/AnalysisPage';
import { DocumentsPage } from './components/DocumentsPage';

// Types
export interface Document {
  id: string;
  filename: string;
  upload_timestamp: string;
  tags: string[];
  category: 'historical_deal' | 'current_opportunity' | 'market_research' | 'portfolio_report' | 'other';
  deal_outcome?: 'invested' | 'passed' | 'exited' | null;
}

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: string;
  analysisType?: 'document_search' | 'investment_analysis';
}

export interface Source {
  filename: string;
  page_number: number;
  chunk_text: string;
  doc_id: string;
  category?: string;
}

export type Page = 'upload' | 'analysis' | 'documents';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('analysis');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      // TODO: Replace with actual API call
      // const response = await fetch('http://localhost:8000/documents');
      // const data = await response.json();
      // setDocuments(data);

      // Mock data for demonstration
      const mockDocs: Document[] = [
        {
          id: '1',
          filename: 'TechCorp_Acquisition_2023.pdf',
          upload_timestamp: new Date('2023-06-15').toISOString(),
          tags: ['SaaS', 'Series B', 'Enterprise'],
          category: 'historical_deal',
          deal_outcome: 'invested'
        },
        {
          id: '2',
          filename: 'HealthTech_DD_Report.pdf',
          upload_timestamp: new Date('2023-08-20').toISOString(),
          tags: ['Healthcare', 'AI', 'B2B'],
          category: 'historical_deal',
          deal_outcome: 'passed'
        },
        {
          id: '3',
          filename: 'FinTech_Startup_Deck.pdf',
          upload_timestamp: new Date('2024-11-01').toISOString(),
          tags: ['FinTech', 'Seed', 'Payments'],
          category: 'current_opportunity',
          deal_outcome: null
        },
        {
          id: '4',
          filename: 'SaaS_Market_Analysis_2024.pdf',
          upload_timestamp: new Date('2024-09-10').toISOString(),
          tags: ['Market Research', 'SaaS', 'Trends'],
          category: 'market_research',
          deal_outcome: null
        },
        {
          id: '5',
          filename: 'Fund_III_Q4_Portfolio_Report.pdf',
          upload_timestamp: new Date('2024-12-05').toISOString(),
          tags: ['Q4', 'Portfolio', 'Performance'],
          category: 'portfolio_report',
          deal_outcome: null
        },
        {
          id: '6',
          filename: 'AI_Platform_Investment_Memo.pdf',
          upload_timestamp: new Date('2023-03-12').toISOString(),
          tags: ['AI/ML', 'Series A', 'B2B'],
          category: 'historical_deal',
          deal_outcome: 'invested'
        }
      ];
      setDocuments(mockDocs);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const handleUploadDocuments = async (files: Array<{ file: File; tags: string[]; category: Document['category']; deal_outcome?: Document['deal_outcome'] }>) => {
    setIsLoading(true);
    try {
      for (const fileData of files) {
        const formData = new FormData();
        formData.append('file', fileData.file);
        formData.append('tags', JSON.stringify(fileData.tags));
        formData.append('category', fileData.category);
        if (fileData.deal_outcome) {
          formData.append('deal_outcome', fileData.deal_outcome);
        }

        // TODO: Replace with actual API call
        // const response = await fetch('http://localhost:8000/upload', {
        //   method: 'POST',
        //   body: formData,
        // });
        // const data = await response.json();

        // Mock response
        const newDoc: Document = {
          id: Date.now().toString() + Math.random(),
          filename: fileData.file.name,
          upload_timestamp: new Date().toISOString(),
          tags: fileData.tags,
          category: fileData.category,
          deal_outcome: fileData.deal_outcome || null
        };

        setDocuments(prev => [...prev, newDoc]);
      }
      
      await fetchDocuments();
    } catch (error) {
      console.error('Error uploading documents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    try {
      // TODO: Replace with actual API call
      // await fetch(`http://localhost:8000/documents/${docId}`, {
      //   method: 'DELETE',
      // });

      setDocuments(prev => prev.filter(doc => doc.id !== docId));
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  };

  const handleSendMessage = async (
    query: string,
    analysisType: 'document_search' | 'investment_analysis',
    selectedDocIds?: string[]
  ) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: query,
      timestamp: new Date().toISOString(),
      analysisType
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // TODO: Replace with actual API call
      // const response = await fetch('http://localhost:8000/chat', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     query: query,
      //     analysis_type: analysisType,
      //     doc_ids: selectedDocIds
      //   })
      // });
      // const data = await response.json();

      // Mock response based on analysis type
      let mockContent = '';
      let mockSources: Source[] = [];

      if (analysisType === 'investment_analysis') {
        mockContent = `**Investment Pattern Analysis:**

Based on your historical investment decisions, here's my assessment:

**Your Investment Thesis (from past deals):**
- Strong preference for B2B SaaS and Enterprise software (70% of invested deals)
- Tendency to invest in Series A-B rounds with proven product-market fit
- Focus on companies with recurring revenue models and 100%+ NRR
- Passed on early-stage healthcare deals citing regulatory concerns

**Analysis of Current Opportunity:**
This FinTech opportunity aligns well with your investment criteria:

✅ **Positive Signals:**
- B2B model matches your preference (similar to TechCorp acquisition)
- Payments infrastructure has strong unit economics
- Experienced founding team with prior exits

⚠️ **Considerations:**
- Seed stage is earlier than your typical entry point
- Competitive landscape requires careful positioning
- You historically prefer Series A+ with $2M+ ARR

**Recommendation:** Consider a smaller initial check with pro-rata rights for Series A, similar to your approach in the AI Platform deal (2023).

**Sources:** TechCorp_Acquisition_2023.pdf (Investment Memo, Pg 3-5), HealthTech_DD_Report.pdf (Pass Decision Rationale, Pg 12), AI_Platform_Investment_Memo.pdf (Deal Terms, Pg 8)`;

        mockSources = [
          {
            filename: 'TechCorp_Acquisition_2023.pdf',
            page_number: 4,
            chunk_text: '## Investment Rationale\n\nTechCorp demonstrates strong B2B SaaS fundamentals:\n- ARR: $5.2M (150% YoY growth)\n- Net Revenue Retention: 125%\n- Enterprise customers: 45 (avg contract $115K)\n- Gross Margin: 82%\n\nDecision: INVEST ($3M Series B)',
            doc_id: '1',
            category: 'historical_deal'
          },
          {
            filename: 'HealthTech_DD_Report.pdf',
            page_number: 12,
            chunk_text: '## Pass Decision Summary\n\nWhile the technology is promising, we are passing due to:\n1. Regulatory pathway uncertainty (FDA clearance timeline)\n2. Early revenue traction ($200K ARR)\n3. Clinical validation requirements delay scalability\n\nDecision: PASS',
            doc_id: '2',
            category: 'historical_deal'
          },
          {
            filename: 'AI_Platform_Investment_Memo.pdf',
            page_number: 8,
            chunk_text: '## Deal Structure\n\nInvestment: $2M at $15M post-money\nStructure: Series A Preferred with 2x pro-rata rights\nKey Terms: Board seat, standard protective provisions\n\nRationale: Smaller initial check given competitive round, with option to increase in Series B',
            doc_id: '6',
            category: 'historical_deal'
          }
        ];
      } else {
        // Document search mode
        mockContent = `Based on the Q4 2024 portfolio report:\n\n**Fund III Performance Summary:**\n- Total Portfolio Value: $125M (1.8x MOIC)\n- Top Performer: TechCorp (3.2x current valuation)\n- Realized Returns: $18M from partial exits\n- Unrealized Gains: $45M mark-to-market\n\n**Key Metrics:**\n| Metric | Q3 2024 | Q4 2024 | Change |\n|--------|---------|---------|--------|\n| NAV | $118M | $125M | +5.9% |\n| IRR | 22% | 24% | +2pp |\n| DPI | 0.4x | 0.45x | +0.05x |\n\n**Sources:** Fund_III_Q4_Portfolio_Report.pdf (Pages 3, 7)`;

        mockSources = [
          {
            filename: 'Fund_III_Q4_Portfolio_Report.pdf',
            page_number: 3,
            chunk_text: '# Q4 2024 Performance Overview\n\nFund III delivered strong performance with NAV increasing to $125M, representing 1.8x MOIC. Top performer TechCorp marked up to 3.2x following Series C raise at $180M valuation.',
            doc_id: '5',
            category: 'portfolio_report'
          }
        ];
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: mockContent,
        sources: mockSources,
        timestamp: new Date().toISOString(),
        analysisType
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, there was an error processing your request.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Navigation currentPage={currentPage} onNavigate={setCurrentPage} documents={documents} />
      
      <div className="flex-1 overflow-hidden">
        {currentPage === 'upload' && (
          <UploadPage onUpload={handleUploadDocuments} isLoading={isLoading} />
        )}
        
        {currentPage === 'analysis' && (
          <AnalysisPage
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            documents={documents}
          />
        )}
        
        {currentPage === 'documents' && (
          <DocumentsPage
            documents={documents}
            onDelete={handleDeleteDocument}
            onRefresh={fetchDocuments}
          />
        )}
      </div>
    </div>
  );
}

export default App;
