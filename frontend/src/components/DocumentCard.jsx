import React from 'react';
import { Link } from 'react-router-dom';

const DocumentCard = ({ document }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const kb = bytes / 1024;
    const mb = kb / 1024;
    if (mb >= 1) return `${mb.toFixed(2)} MB`;
    return `${kb.toFixed(2)} KB`;
  };

  const getFileIcon = (fileType) => {
    switch (fileType?.toLowerCase()) {
      case 'pdf':
        return '📄';
      case 'docx':
      case 'doc':
        return '📝';
      case 'pptx':
      case 'ppt':
        return '📊';
      case 'xlsx':
      case 'xls':
        return '📈';
      default:
        return '📎';
    }
  };

  const getFileTypeColor = (fileType) => {
    switch (fileType?.toLowerCase()) {
      case 'pdf':
        return 'bg-burgundy/10 text-burgundy';
      case 'docx':
      case 'doc':
        return 'bg-teal/10 text-teal';
      case 'pptx':
      case 'ppt':
        return 'bg-gold/10 text-gold';
      case 'xlsx':
      case 'xls':
        return 'bg-teal/10 text-teal';
      default:
        return 'bg-ink/10 text-ink';
    }
  };

  return (
    <Link to={`/documents/${document.id}`}>
      <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition cursor-pointer border border-transparent hover:border-teal">
        <div className="flex items-start space-x-4">
          <div className="text-4xl">{getFileIcon(document.file_type)}</div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-heading font-bold text-ink mb-2 truncate">
              {document.file_name}
            </h3>
            <div className="flex flex-wrap gap-2 mb-3">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium ${getFileTypeColor(document.file_type)}`}>
                {document.file_type?.toUpperCase()}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium bg-ink/10 text-ink">
                {formatFileSize(document.file_size)}
              </span>
              {document.language_detected && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium bg-teal/10 text-teal">
                  {document.language_detected.toUpperCase()}
                </span>
              )}
            </div>
            <p className="text-sm font-body text-ink/60">
              Uploaded: {formatDate(document.uploaded_at)}
            </p>
          </div>
        </div>

        {(document.extracted_text || document.extracted_tables_json || document.extracted_charts_json || document.financial_data_json) && (
          <div className="mt-4 pt-4 border-t border-ink/10">
            <p className="text-xs font-body text-teal font-medium">✓ AI extraction completed</p>
          </div>
        )}
      </div>
    </Link>
  );
};

export default DocumentCard;