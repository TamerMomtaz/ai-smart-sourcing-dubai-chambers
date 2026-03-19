import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const FILE_TYPE_STYLES = {
  pdf: { color: 'text-red-400 bg-red-500/20 border-red-500/30', label: 'PDF' },
  docx: { color: 'text-blue-400 bg-blue-500/20 border-blue-500/30', label: 'DOCX' },
  pptx: { color: 'text-orange-400 bg-orange-500/20 border-orange-500/30', label: 'PPTX' },
  xlsx: { color: 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30', label: 'XLSX' },
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
    api.get('/api/v1/proposals?page_size=100').then(({ data }) => {
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
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#3B82F6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading documents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F172A] p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-white">Documents</h1>
          <p className="text-gray-400 text-sm mt-1">All uploaded documents across proposals</p>
        </header>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Search and filters */}
        <div className="bg-[#1E293B] rounded-xl p-4 mb-6 flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="Search by filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6] w-64"
          />
          <select
            value={fileTypeFilter}
            onChange={(e) => { setFileTypeFilter(e.target.value); setSearchParams({ page: '1' }); }}
            className="bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
          >
            <option value="">All Types</option>
            <option value="pdf">PDF</option>
            <option value="docx">DOCX</option>
            <option value="pptx">PPTX</option>
            <option value="xlsx">XLSX</option>
          </select>
        </div>

        <div className="bg-[#1E293B] rounded-xl overflow-hidden shadow-xl">
          <table className="w-full">
            <thead className="bg-[#0F172A] border-b border-gray-700">
              <tr>
                <th className="text-left p-4 text-gray-400 font-medium text-sm">File Name</th>
                <th className="text-left p-4 text-gray-400 font-medium text-sm">Proposal</th>
                <th className="text-left p-4 text-gray-400 font-medium text-sm">Type</th>
                <th className="text-left p-4 text-gray-400 font-medium text-sm">Size</th>
                <th className="text-left p-4 text-gray-400 font-medium text-sm">Uploaded</th>
                <th className="text-left p-4 text-gray-400 font-medium text-sm">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center p-12">
                    <p className="text-[#94A3B8] mb-2">No documents uploaded yet.</p>
                    <p className="text-[#94A3B8] text-sm mb-4">Upload documents from the Proposal detail view — click 'View' on any proposal to upload supporting files.</p>
                    <Link
                      to="/proposals"
                      className="inline-block bg-[#3B82F6] text-white px-5 py-2 rounded-lg font-semibold hover:bg-blue-600 transition-colors text-sm"
                    >
                      Go to Proposals
                    </Link>
                  </td>
                </tr>
              ) : (
                filteredDocs.map((d) => {
                  const typeInfo = FILE_TYPE_STYLES[d.file_type] || FILE_TYPE_STYLES.pdf;
                  return (
                    <tr key={d.id} className="border-b border-gray-700/50 hover:bg-[#0F172A]/50 transition-colors">
                      <td className="p-4 text-white font-medium">{d.file_name}</td>
                      <td className="p-4 text-sm">
                        {d.proposal_id ? (
                          <Link to={`/proposals/${d.proposal_id}`} className="text-[#3B82F6] hover:text-blue-300">
                            {proposals[d.proposal_id] || d.proposal_id?.slice(0, 8) + '...'}
                          </Link>
                        ) : (
                          <span className="text-gray-500">—</span>
                        )}
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold border ${typeInfo.color}`}>
                          {typeInfo.label}
                        </span>
                      </td>
                      <td className="p-4 text-gray-400 text-sm">{formatFileSize(d.file_size)}</td>
                      <td className="p-4 text-gray-400 text-sm">
                        {d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="p-4">
                        <button
                          onClick={() => handleDownload(d.id)}
                          className="text-[#3B82F6] hover:text-blue-300 text-sm font-medium"
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
          <div className="flex items-center justify-center space-x-3 mt-6">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
              className="px-4 py-2 rounded-lg bg-[#1E293B] text-gray-300 border border-gray-700 disabled:opacity-40 hover:bg-gray-700 transition"
            >
              Previous
            </button>
            <span className="text-gray-400">
              Page {page} of {pagination.total_pages}
            </span>
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page === pagination.total_pages}
              className="px-4 py-2 rounded-lg bg-[#1E293B] text-gray-300 border border-gray-700 disabled:opacity-40 hover:bg-gray-700 transition"
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
