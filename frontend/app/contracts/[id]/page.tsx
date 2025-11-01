'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import axios from 'axios';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ContractData {
  contract_id: string;
  filename: string;
  status: string;
  completeness_score: number;
  score_breakdown?: {
    financial_completeness: number;
    party_identification: number;
    payment_terms: number;
    sla_definition: number;
    contact_information: number;
  };
  missing_fields: string[];
  customer?: {
    name: string;
    legal_entity?: string;
    address?: string;
  };
  vendor?: {
    name: string;
    legal_entity?: string;
    address?: string;
  };
  financial_details?: {
    total_value: number;
    currency: string;
    line_items: any[];
  };
  payment_structure?: {
    payment_terms: string;
    schedules: any[];
  };
  revenue_classification?: {
    recurring_payment: boolean;
    one_time_payment: boolean;
    billing_cycle?: string;
  };
  sla?: {
    performance_metrics: any[];
    support_terms?: string;
  };
  upload_date: string;
  processing_time_seconds?: number;
}

export default function ContractDetailPage() {
  const params = useParams();
  const router = useRouter();
  const contractId = params.id as string;
  
  const [contract, setContract] = useState<ContractData | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkingStatus, setCheckingStatus] = useState(false);

  useEffect(() => {
    fetchContract();
    const interval = setInterval(() => {
      if (contract?.status === 'pending' || contract?.status === 'processing') {
        fetchContract();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [contractId, contract?.status]);

  const fetchContract = async () => {
    try {
      setLoading(true);
      
      // First check status
      const statusResponse = await axios.get(`${API_URL}/contracts/${contractId}/status`);
      
      if (statusResponse.data.status === 'completed') {
        const contractResponse = await axios.get(`${API_URL}/contracts/${contractId}`);
        setContract(contractResponse.data);
      } else {
        // If still processing, show status info
        setContract({
          ...statusResponse.data,
          contract_id: contractId,
          filename: '',
          completeness_score: 0,
          missing_fields: [],
          upload_date: statusResponse.data.upload_date,
        } as any);
      }
    } catch (error: any) {
      if (error.response?.status === 202) {
        // Still processing
        const statusResponse = await axios.get(`${API_URL}/contracts/${contractId}/status`);
        setContract({
          ...statusResponse.data,
          contract_id: contractId,
          filename: '',
          completeness_score: 0,
          missing_fields: [],
          upload_date: statusResponse.data.upload_date,
        } as any);
      } else {
        console.error('Error fetching contract:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    window.open(`${API_URL}/contracts/${contractId}/download`, '_blank');
  };

  if (loading && !contract) {
    return (
      <div className="flex min-h-screen bg-white">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-600">Loading contract details...</div>
        </div>
      </div>
    );
  }

  const statusColor = 
    contract?.status === 'completed' ? 'bg-green-500' :
    contract?.status === 'processing' ? 'bg-blue-500' :
    contract?.status === 'failed' ? 'bg-red-500' :
    'bg-gray-500';

  return (
    <div className="flex min-h-screen bg-white">
      <Sidebar />
      
      <div className="flex-1 flex flex-col">
        <Header 
          searchTerm=""
          onSearchChange={() => {}}
          onSearch={() => {}}
          onRefresh={fetchContract}
        />
        
        <main className="flex-1 p-8 overflow-auto">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-800">Contract Details</h1>
            <button
              onClick={handleDownload}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>
          </div>

          {contract?.status === 'processing' || contract?.status === 'pending' ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
              <div className="mb-4">
                <div className={`inline-block px-3 py-1 rounded-full text-white text-sm font-medium ${statusColor}`}>
                  {contract.status.charAt(0).toUpperCase() + contract.status.slice(1)}
                </div>
              </div>
              <p className="text-gray-600 mb-2">Processing contract...</p>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${contract.progress || 0}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-500">Progress: {contract.progress || 0}%</p>
            </div>
          ) : contract?.status === 'failed' ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-red-800 mb-2">Processing Failed</h2>
              <p className="text-red-600">{contract.error_message || 'Unknown error occurred'}</p>
            </div>
          ) : contract ? (
            <div className="space-y-6">
              {/* Overview Card */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Overview</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Status</p>
                    <span className={`inline-block px-3 py-1 rounded-full text-white text-sm font-medium mt-1 ${statusColor}`}>
                      {contract.status}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Score</p>
                    <p className="text-xl font-bold text-gray-800">{contract.completeness_score.toFixed(1)}/100</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Upload Date</p>
                    <p className="text-gray-800">{new Date(contract.upload_date).toLocaleDateString()}</p>
                  </div>
                  {contract.processing_time_seconds && (
                    <div>
                      <p className="text-sm text-gray-500">Processing Time</p>
                      <p className="text-gray-800">{contract.processing_time_seconds.toFixed(2)}s</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Score Breakdown */}
              {contract.score_breakdown && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Score Breakdown</h2>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-700">Financial Completeness</span>
                        <span className="text-gray-800 font-medium">{contract.score_breakdown.financial_completeness.toFixed(1)}/30</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(contract.score_breakdown.financial_completeness / 30) * 100}%` }}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-700">Party Identification</span>
                        <span className="text-gray-800 font-medium">{contract.score_breakdown.party_identification.toFixed(1)}/25</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(contract.score_breakdown.party_identification / 25) * 100}%` }}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-700">Payment Terms</span>
                        <span className="text-gray-800 font-medium">{contract.score_breakdown.payment_terms.toFixed(1)}/20</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(contract.score_breakdown.payment_terms / 20) * 100}%` }}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-700">SLA Definition</span>
                        <span className="text-gray-800 font-medium">{contract.score_breakdown.sla_definition.toFixed(1)}/15</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(contract.score_breakdown.sla_definition / 15) * 100}%` }}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-700">Contact Information</span>
                        <span className="text-gray-800 font-medium">{contract.score_breakdown.contact_information.toFixed(1)}/10</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(contract.score_breakdown.contact_information / 10) * 100}%` }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Parties */}
              {(contract.customer || contract.vendor) && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Parties</h2>
                  <div className="grid md:grid-cols-2 gap-6">
                    {contract.customer && (
                      <div>
                        <h3 className="font-semibold text-gray-700 mb-2">Customer</h3>
                        <p className="text-gray-800">{contract.customer.name}</p>
                        {contract.customer.legal_entity && (
                          <p className="text-sm text-gray-600 mt-1">{contract.customer.legal_entity}</p>
                        )}
                        {contract.customer.address && (
                          <p className="text-sm text-gray-600 mt-1">{contract.customer.address}</p>
                        )}
                      </div>
                    )}
                    {contract.vendor && (
                      <div>
                        <h3 className="font-semibold text-gray-700 mb-2">Vendor</h3>
                        <p className="text-gray-800">{contract.vendor.name}</p>
                        {contract.vendor.legal_entity && (
                          <p className="text-sm text-gray-600 mt-1">{contract.vendor.legal_entity}</p>
                        )}
                        {contract.vendor.address && (
                          <p className="text-sm text-gray-600 mt-1">{contract.vendor.address}</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Financial Details */}
              {contract.financial_details && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Financial Details</h2>
                  <div className="space-y-2">
                    {contract.financial_details.total_value && (
                      <div className="flex justify-between">
                        <span className="text-gray-700">Total Value</span>
                        <span className="text-gray-800 font-semibold">
                          {contract.financial_details.currency || 'USD'} {contract.financial_details.total_value.toLocaleString()}
                        </span>
                      </div>
                    )}
                    {contract.financial_details.line_items && contract.financial_details.line_items.length > 0 && (
                      <div className="mt-4">
                        <h3 className="font-semibold text-gray-700 mb-2">Line Items</h3>
                        <div className="space-y-2">
                          {contract.financial_details.line_items.slice(0, 5).map((item: any, index: number) => (
                            <div key={index} className="border-l-4 border-blue-500 pl-3 py-2 bg-gray-50">
                              <p className="text-gray-800">{item.description}</p>
                              {item.quantity && item.unit_price && (
                                <p className="text-sm text-gray-600">
                                  Qty: {item.quantity} × {item.unit_price} = {item.total_price || item.quantity * item.unit_price}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Payment Structure */}
              {contract.payment_structure && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Payment Structure</h2>
                  <div className="space-y-2">
                    {contract.payment_structure.payment_terms && (
                      <p className="text-gray-800">
                        <span className="font-semibold">Payment Terms:</span> {contract.payment_structure.payment_terms}
                      </p>
                    )}
                    {contract.revenue_classification && (
                      <div className="mt-3">
                        <p className="text-gray-700">
                          <span className="font-semibold">Payment Type:</span>{' '}
                          {contract.revenue_classification.recurring_payment && 'Recurring'}
                          {contract.revenue_classification.recurring_payment && contract.revenue_classification.one_time_payment && ' + '}
                          {contract.revenue_classification.one_time_payment && 'One-time'}
                        </p>
                        {contract.revenue_classification.billing_cycle && (
                          <p className="text-gray-600 text-sm mt-1">
                            Billing Cycle: {contract.revenue_classification.billing_cycle}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Missing Fields */}
              {contract.missing_fields && contract.missing_fields.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                  <h2 className="text-xl font-bold text-yellow-800 mb-4">Missing Fields</h2>
                  <ul className="list-disc list-inside space-y-1">
                    {contract.missing_fields.map((field, index) => (
                      <li key={index} className="text-yellow-700">{field}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : null}
        </main>
      </div>
    </div>
  );
}

