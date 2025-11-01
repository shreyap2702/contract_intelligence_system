'use client';

import { useRouter } from 'next/navigation';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ContractCardProps {
  contract: {
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
  };
}

export default function ContractCard({ contract }: ContractCardProps) {
  const router = useRouter();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'processing':
        return 'bg-blue-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    window.open(`${API_URL}/contracts/${contract.contract_id}/download`, '_blank');
  };

  const handleCardClick = () => {
    router.push(`/contracts/${contract.contract_id}`);
  };

  // Truncate filename
  const truncatedFilename =
    contract.filename.length > 40
      ? contract.filename.substring(0, 40) + '...'
      : contract.filename;

  // Generate description from available data
  const description = contract.contract_type || 
    (contract.customer_name ? `Contract with ${contract.customer_name}` : 'Contract document');

  // Generate tags
  const tags = [];
  if (contract.contract_type) tags.push(contract.contract_type);
  if (contract.customer_name) tags.push('Customer');
  if (contract.vendor_name) tags.push('Vendor');
  if (contract.total_value) tags.push('Financial');
  if (contract.status === 'completed') tags.push('Processed');

  return (
    <div
      onClick={handleCardClick}
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 cursor-pointer hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-bold text-gray-800 flex-1 pr-2">
          {truncatedFilename}
        </h3>
        <span
          className={`px-3 py-1 rounded-full text-white text-xs font-medium ${getStatusColor(
            contract.status
          )}`}
        >
          {contract.status.toUpperCase()}
        </span>
      </div>

      <div className="mb-4">
        <span className="inline-block px-2 py-1 rounded bg-red-500 text-white text-xs font-medium mb-2">
          PDF
        </span>
        <p className="text-gray-600 text-sm mt-2 line-clamp-2">{description}</p>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {tags.slice(0, 4).map((tag, index) => (
          <span
            key={index}
            className="px-2 py-1 rounded-full bg-gray-100 text-gray-700 text-xs"
          >
            {tag}
          </span>
        ))}
        {tags.length > 4 && (
          <span className="px-2 py-1 rounded-full bg-gray-100 text-gray-700 text-xs">
            +{tags.length - 4}
          </span>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Score: <span className="font-semibold text-gray-800">{contract.completeness_score.toFixed(1)}</span>
          {contract.total_value && (
            <span className="ml-3">
              Value: <span className="font-semibold text-gray-800">
                {contract.currency || 'USD'} {contract.total_value.toLocaleString()}
              </span>
            </span>
          )}
        </div>
        <button
          onClick={handleDownload}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2 text-sm font-medium transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download
        </button>
      </div>
    </div>
  );
}

