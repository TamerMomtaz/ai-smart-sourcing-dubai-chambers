import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';
import Pagination from '../components/Pagination';

const DESCCertifiedProvidersList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [providers, setProviders] = useState([]);
  const [pagination, setPagination] = useState(null);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20;

  useEffect(() => {
    fetchProviders();
  }, [page]);

  const fetchProviders = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/api/v1/desc-certified-providers?page=${page}&page_size=${pageSize}`);
      setProviders(res.data.providers || []);
      setPagination(res.data.pagination);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage) => {
    setSearchParams({ page: newPage.toString() });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" text="Loading providers..." />
      </div>
    );
  }

  return (
    <div>
      <h1 className="font-heading text-3xl text-ink mb-6">DESC Certified Providers</h1>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {providers.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-8 text-center">
          <p className="text-ink/60 font-body">No certified providers found.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-cream">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-body font-medium text-ink">Provider</th>
                <th className="px-6 py-3 text-left text-sm font-body font-medium text-ink">Certification #</th>
                <th className="px-6 py-3 text-left text-sm font-body font-medium text-ink">Valid Until</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cream">
              {providers.map((provider) => (
                <tr key={provider.id} className="hover:bg-cream/50">
                  <td className="px-6 py-4 font-body text-ink">{provider.provider_name}</td>
                  <td className="px-6 py-4 font-body text-ink/70">{provider.certification_number}</td>
                  <td className="px-6 py-4 font-body text-ink/70">
                    {new Date(provider.valid_until).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pagination && (
        <Pagination
          currentPage={page}
          totalPages={pagination.total_pages || 1}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
};

export default DESCCertifiedProvidersList;
