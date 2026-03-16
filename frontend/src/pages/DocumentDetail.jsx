import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import LoadingSpinner from '../components/LoadingSpinner';

const DocumentDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloadLoading, setDownloadLoading] = useState(false);

  useEffect(() => {
    fetchDocument();
    fetchExtractedData();
  }, [id]);

  const fetchDocument = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/documents/${id}`);
      setDocument(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const fetchExtractedData = async () => {
    try {
      const { data } = await api.get(`/api/v1/documents/${id}/extracted-data`);
      setExtractedData(data);
    } catch (err) {
      console.error('Failed to fetch extracted data:', err);
    }
  };

  const handleDownload = async () => {
    try {
      setDownloadLoading(true);
      const { data } = await api.get(`/api/v1/documents/${id}/download`);
      window.open(data.download_url, '_blank');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDownloadLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" text="Loading document..." />
      </div>
    );
  }

  if (error && !document) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-burgundy font-body text-lg">{error}</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-heading text-4xl text-ink">{document.file_name}</h1>
        <button
          onClick={() => navigate('/documents')}
          className="px-4 py-2 border border-ink/20 rounded-lg font-body text-ink hover:bg-cream transition"
        >
          Back to Documents
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h2 className="font-heading text-2xl text-teal mb-4">Document Info</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-ink/60 font-body">File Type</p>
            <p className="font-body text-ink">{document.file_type?.toUpperCase()}</p>
          </div>
          <div>
            <p className="text-sm text-ink/60 font-body">File Size</p>
            <p className="font-body text-ink">{(document.file_size / 1024).toFixed(1)} KB</p>
          </div>
          <div>
            <p className="text-sm text-ink/60 font-body">Language</p>
            <p className="font-body text-ink">{document.language_detected || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-ink/60 font-body">Uploaded</p>
            <p className="font-body text-ink">{new Date(document.uploaded_at).toLocaleString()}</p>
          </div>
        </div>
        <button
          onClick={handleDownload}
          disabled={downloadLoading}
          className="mt-4 px-6 py-2 bg-teal text-white rounded-lg font-body hover:bg-teal/90 transition disabled:opacity-50"
        >
          {downloadLoading ? 'Downloading...' : 'Download'}
        </button>
      </div>

      {extractedData && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="font-heading text-2xl text-teal mb-4">Extracted Data</h2>
          {extractedData.extracted_text && (
            <div className="mb-4">
              <h3 className="font-body font-medium text-ink mb-2">Extracted Text</h3>
              <pre className="bg-cream rounded-lg p-4 text-sm font-mono text-ink/80 whitespace-pre-wrap max-h-96 overflow-y-auto">
                {extractedData.extracted_text}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentDetail;
