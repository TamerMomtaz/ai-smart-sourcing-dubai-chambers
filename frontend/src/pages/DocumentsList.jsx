import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const FILE_TYPE_STYLES = {
  pdf: { color: 'text-red-500 bg-red-100 border-red-200', label: 'PDF' },
  docx: { color: 'text-blue-600 bg-blue-100 border-blue-200', label: 'DOCX' },
  pptx: { color: 'text-orange-500 bg-orange-100 border-orange-200', label: 'PPTX' },
  xlsx: { color: 'text-emerald-600 bg-emerald-100 border-emerald-200', label: 'XLSX' },
};

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const DocumentsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [search, setSearch] = useState('');
  const [fileTypeFilter, setFileTypeFilter] = useState('');
  const [proposals, setProposals] = useState({});

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 30;

  useEffect(() => {
    fetchDocuments();
  }, [page, fileTypeFilter]);

  useEffect(() => {
    // Fetch proposals for title mapping
    api.get('/api/v1/chamber_proposals?page_size=200').then(({ data }) => {
      const map = {};
      const items = data.proposals || data.data || [];
      items.forEach((p) => { map[p.id] = p.title; });
      setProposals(map);
    }).catch(() => {});
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      let url = `/api/v1/chamber-documents?page=${page}&page_size=${pageSize}`;
      if (fileTypeFilter) url += `&file_type=${fileTypeFilter}`;
      const res = await api.get(url);
      setDocuments(res.data.documents || []);
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

  const handleDownload = async (docId) => {
    try {
      const { data } = await api.get(`/api/v1/chamber-documents/${docId}/download`);
      if (data.download_url) {
        window.open(data.download_url, '_blank');
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const filteredDocs = search
    ? documents.filter((d) => d.file_name.toLowerCase().includes(search.toLowerCase()))
    : documents;

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="animate-pulse text-teal font-heading text-2xl">Loading documents...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="font-heading text-4xl text-teal">Documents</h1>
        </header>

        {error && (
          <div className="bg-burgundy/10 border border-burgundy rounded-lg p-4 mb-6">
            <p className="text-burgundy">{error}</p>
          </div>
        )}

        {/* Search and filters */}
        <div className="flex flex-wrap gap-3 mb-6">
          <input
            type="text"
            placeholder="Search by filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-4 py-2 rounded-lg border border-ink/20 bg-white text-ink focus:outline-none focus:ring-2 focus:ring-teal/50 w-64"
          />
          <select
            value={fileTypeFilter}
            onChange={(e) => { setFileTypeFilter(e.target.value); setSearchParams({ page: '1' }); }}
            className="px-4 py-2 rounded-lg border border-ink/20 bg-white text-ink focus:outline-none focus:ring-2 focus:ring-teal/50"
          >
            <option value="">All Types</option>
            <option value="pdf">PDF</option>
            <option value="docx">DOCX</option>
            <option value="pptx">PPTX</option>
            <option value="xlsx">XLSX</option>
          </select>
        </div>

        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-teal text-white">
              <tr>
                <th className="text-left p-4">File Name</th>
                <th className="text-left p-4">Proposal</th>
                <th className="text-left p-4">Type</th>
                <th className="text-left p-4">Size</th>
                <th className="text-left p-4">Uploaded</th>
                <th className="text-left p-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center p-8 text-ink/60">
                    No documents found
                  </td>
                </tr>
              ) : (
                filteredDocs.map((d) => {
                  const typeInfo = FILE_TYPE_STYLES[d.file_type] || FILE_TYPE_STYLES.pdf;
                  return (
                    <tr key={d.id} className="border-b border-cream hover:bg-cream/50">
                      <td className="p-4 font-medium">{d.file_name}</td>
                      <td className="p-4 text-sm text-ink/70">
                        {proposals[d.proposal_id] || d.proposal_id?.slice(0, 8) + '...'}
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold border ${typeInfo.color}`}>
                          {typeInfo.label}
                        </span>
                      </td>
                      <td className="p-4 text-sm">{formatFileSize(d.file_size)}</td>
                      <td className="p-4 text-sm">
                        {d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="p-4">
                        <button
                          onClick={() => handleDownload(d.id)}
                          className="text-teal hover:underline text-sm font-medium"
                        >
                          Download
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center space-x-2 mt-6">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
              className="px-4 py-2 rounded-lg bg-white border border-cream disabled:opacity-50 hover:bg-cream transition"
            >
              Previous
            </button>
            <span className="text-ink">
              Page {page} of {pagination.total_pages}
            </span>
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page === pagination.total_pages}
              className="px-4 py-2 rounded-lg bg-white border border-cream disabled:opacity-50 hover:bg-cream transition"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentsList;
