'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import ContractCard from '@/components/ContractCard';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Contract {
  contract_id: string;
  filename: string;
  status: string;
  upload_date: string;
  completeness_score: number;
  total_value?: number;
  currency?: string;
  customer_name?: string;
  vendor_name?: string;
  contract_type?: string;
}

export default function Home() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [minScore, setMinScore] = useState<number | null>(null);

  const router = useRouter();

  useEffect(() => {
    fetchContracts();
  }, [filterStatus, minScore]);

  const fetchContracts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterStatus) params.append('status', filterStatus);
      if (minScore !== null) params.append('min_score', minScore.toString());
      
      const response = await axios.get(`${API_URL}/contracts?${params.toString()}`);
      setContracts(response.data.contracts || []);
    } catch (error) {
      console.error('Error fetching contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filterStatus) params.append('status', filterStatus);
      if (minScore !== null) params.append('min_score', minScore.toString());
      
      const response = await axios.get(`${API_URL}/contracts?${params.toString()}`);
      setContracts(response.data.contracts || []);
    } catch (error) {
      console.error('Error searching contracts:', error);
    }
  };

  const filteredContracts = contracts.filter(contract => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      contract.filename.toLowerCase().includes(search) ||
      contract.customer_name?.toLowerCase().includes(search) ||
      contract.vendor_name?.toLowerCase().includes(search)
    );
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'processing': return 'bg-blue-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="flex min-h-screen bg-white">
      <Sidebar />
      
      <div className="flex-1 flex flex-col">
        <Header 
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onSearch={handleSearch}
          onRefresh={fetchContracts}
        />
        
        <main className="flex-1 p-8 overflow-auto">
          <h1 className="text-3xl font-bold text-gray-800 mb-8">Dashboard</h1>
          
          {/* Filters */}
          <div className="mb-6 flex gap-4 items-center">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
            
            <input
              type="number"
              placeholder="Min Score"
              value={minScore || ''}
              onChange={(e) => setMinScore(e.target.value ? Number(e.target.value) : null)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 w-32"
              min="0"
              max="100"
            />
          </div>

          {/* Contracts Section */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Contracts</h2>
            
            {loading ? (
              <div className="text-gray-600">Loading contracts...</div>
            ) : filteredContracts.length === 0 ? (
              <div className="text-gray-600">No contracts found. Upload a contract to get started.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {filteredContracts.map((contract) => (
                  <ContractCard key={contract.contract_id} contract={contract} />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

