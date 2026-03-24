import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../lib/api';

function formatDate(iso) {
  if (!iso) return 'N/A';
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'long', year: 'numeric',
    });
  } catch { return iso; }
}

function statusColor(status) {
  if (status === 'pass') return '#16a34a';
  if (status === 'warning') return '#d97706';
  return '#dc2626';
}

function statusBg(status) {
  if (status === 'pass') return '#dcfce7';
  if (status === 'warning') return '#fef9c3';
  return '#fee2e2';
}

function scoreColorClass(score) {
  if (score >= 80) return 'score-high';
  if (score >= 60) return 'score-mid';
  return 'score-low';
}

function riskBadgeStyle(level) {
  if (level === 'low') return { background: '#dcfce7', color: '#166534' };
  if (level === 'medium') return { background: '#fef9c3', color: '#854d0e' };
  return { background: '#fee2e2', color: '#991b1b' };
}

export default function AuditReport() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get(`/api/v1/compliance-audits/${id}/report-data`)
      .then(res => setData(res.data))
      .catch(err => setError(err?.response?.data?.detail || 'Failed to load audit report data'))
      .finally(() => setLoading(false));
  }, [id]);

  const handlePrint = () => window.print();

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#fff' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: 48, height: 48, border: '4px solid #e5e7eb', borderTopColor: '#0D9488', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
          <p style={{ color: '#6b7280' }}>Preparing Compliance Audit Report...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#fff' }}>
        <div style={{ textAlign: 'center', color: '#dc2626' }}>
          <p style={{ fontSize: 18, fontWeight: 600 }}>Error</p>
          <p>{typeof error === 'string' ? error : JSON.stringify(error)}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const {
    audit_id, proposal_title, vendor_name, sector, audit_date, auditor,
    overall_score, compliance_label, risk_level, summary,
    total_pass, total_fail, total_warnings,
    frameworks, remediation_items, remediation_required,
    lifecycle_phases, data_residency, hash_chain_signature,
  } = data;

  return (
    <>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @media print {
          .no-print { display: none !important; }
          body { margin: 0; padding: 0; background: #fff !important; }
          @page { margin: 18mm 14mm; }
          .report-page { page-break-after: always; }
          .report-page:last-child { page-break-after: auto; }
          .report-container { padding: 0 !important; }
        }
        .report-container {
          max-width: 900px; margin: 0 auto; padding: 32px 24px;
          font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
          color: #1e293b; background: #fff; line-height: 1.5;
        }
        .report-container h1 { font-size: 28px; font-weight: 700; color: #0D9488; margin: 0 0 4px; }
        .report-container h2 { font-size: 18px; font-weight: 700; color: #0D9488; margin: 24px 0 12px; border-bottom: 2px solid #0D9488; padding-bottom: 4px; }
        .report-container h3 { font-size: 15px; font-weight: 600; color: #334155; margin: 16px 0 8px; }
        .subtitle { font-size: 14px; color: #64748b; margin: 0 0 4px; }
        .date-line { font-size: 12px; color: #94a3b8; margin-bottom: 20px; }
        .metrics-row { display: flex; gap: 16px; margin: 16px 0; }
        .metric-card {
          flex: 1; background: #f0fdfa; border: 1px solid #99f6e4; border-radius: 8px;
          padding: 14px; text-align: center;
        }
        .metric-card .value { font-size: 28px; font-weight: 700; color: #0D9488; }
        .metric-card .label { font-size: 12px; color: #64748b; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; margin: 8px 0; }
        th { background: #0D9488; color: #fff; padding: 8px 12px; text-align: left; font-weight: 600; }
        td { padding: 8px 12px; border-bottom: 1px solid #e5e7eb; }
        tr:nth-child(even) td { background: #f8fafc; }
        .score-badge {
          display: inline-block; padding: 2px 10px; border-radius: 12px;
          font-weight: 600; font-size: 13px;
        }
        .score-high { background: #dcfce7; color: #166534; }
        .score-mid { background: #fef9c3; color: #854d0e; }
        .score-low { background: #fee2e2; color: #991b1b; }
        .footer {
          margin-top: 24px; padding-top: 12px; border-top: 1px solid #cbd5e1;
          font-size: 11px; color: #94a3b8; text-align: center;
        }
        .pill { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 4px; }
        .big-score {
          font-size: 72px; font-weight: 800; text-align: center; margin: 16px 0 4px;
        }
        .compliance-label {
          text-align: center; font-size: 20px; font-weight: 700; margin-bottom: 16px;
        }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; font-size: 13px; margin: 12px 0; }
        .info-grid .lbl { color: #64748b; }
        .info-grid .val { color: #1e293b; font-weight: 500; }
        .lifecycle-row { display: flex; gap: 8px; margin: 12px 0; }
        .lifecycle-item {
          flex: 1; text-align: center; border-radius: 8px; padding: 10px 4px;
          border: 1px solid #e5e7eb;
        }
        .lifecycle-item .phase-name { font-size: 11px; font-weight: 600; margin-bottom: 4px; }
        .lifecycle-item .phase-status { font-size: 18px; }
        .remediation-table td:first-child { font-weight: 600; }
        .priority-high { color: #dc2626; font-weight: 600; }
        .priority-medium { color: #d97706; font-weight: 600; }
        .priority-low { color: #16a34a; font-weight: 600; }
      `}</style>

      {/* Print button */}
      <div className="no-print" style={{ position: 'fixed', top: 16, right: 16, zIndex: 100 }}>
        <button
          onClick={handlePrint}
          style={{
            background: '#0D9488', color: '#fff', border: 'none', borderRadius: 8,
            padding: '10px 24px', fontSize: 14, fontWeight: 600, cursor: 'pointer',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          }}
        >
          Save as PDF / Print
        </button>
      </div>

      <div className="report-container">
        {/* ===== PAGE 1: COVER & SUMMARY ===== */}
        <div className="report-page">
          <h1>DESC Compliance Audit Report</h1>
          <p className="subtitle">AI Smart Sourcing &mdash; Dubai Chambers</p>
          <p className="date-line">
            Audit Date: {formatDate(audit_date)} &nbsp;|&nbsp; Audit ID: {audit_id?.slice(0, 8)}
          </p>

          <div className="info-grid">
            <div><span className="lbl">Proposal:</span></div>
            <div><span className="val">{proposal_title}</span></div>
            <div><span className="lbl">Vendor:</span></div>
            <div><span className="val">{vendor_name}</span></div>
            <div><span className="lbl">Sector:</span></div>
            <div><span className="val">{sector || 'N/A'}</span></div>
            <div><span className="lbl">Auditor:</span></div>
            <div><span className="val">{auditor}</span></div>
          </div>

          {/* Overall Score */}
          <div className="big-score" style={{ color: overall_score >= 80 ? '#16a34a' : overall_score >= 60 ? '#d97706' : '#dc2626' }}>
            {overall_score ?? '—'}
          </div>
          <div className="compliance-label" style={{ color: overall_score >= 80 ? '#16a34a' : overall_score >= 60 ? '#d97706' : '#dc2626' }}>
            {compliance_label}
          </div>

          {/* Summary counts */}
          <div className="metrics-row">
            <div className="metric-card">
              <div className="value" style={{ color: '#16a34a' }}>{total_pass}</div>
              <div className="label">Controls Passed</div>
            </div>
            <div className="metric-card">
              <div className="value" style={{ color: '#d97706' }}>{total_warnings}</div>
              <div className="label">Warnings</div>
            </div>
            <div className="metric-card">
              <div className="value" style={{ color: '#dc2626' }}>{total_fail}</div>
              <div className="label">Failures</div>
            </div>
            <div className="metric-card">
              <div className="value">
                <span className={`score-badge ${scoreColorClass(overall_score || 0)}`} style={{ ...riskBadgeStyle(risk_level), fontSize: 14, padding: '4px 12px' }}>
                  {risk_level?.toUpperCase()} RISK
                </span>
              </div>
              <div className="label">Risk Level</div>
            </div>
          </div>

          {/* Summary text */}
          {summary && (
            <>
              <h3>Executive Summary</h3>
              <p style={{ fontSize: 13, color: '#334155' }}>{summary}</p>
            </>
          )}

          <div className="footer">
            DESC Compliance Audit Report | AI Smart Sourcing | Powered by &sigma;I | {formatDate(audit_date)} | Confidential
          </div>
        </div>

        {/* ===== PAGE 2: FRAMEWORK RESULTS ===== */}
        <div className="report-page">
          <h2>Framework Results</h2>

          {frameworks.map((fw, idx) => (
            <div key={idx} style={{ marginBottom: 24 }}>
              <h3 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{fw.name}</span>
                <span className={`score-badge ${scoreColorClass(fw.sub_score)}`}>
                  Score: {fw.sub_score}
                </span>
              </h3>
              <table>
                <thead>
                  <tr>
                    <th style={{ width: '25%' }}>Control</th>
                    <th style={{ width: '12%' }}>Status</th>
                    <th style={{ width: '33%' }}>Evidence</th>
                    <th style={{ width: '30%' }}>Recommendation</th>
                  </tr>
                </thead>
                <tbody>
                  {fw.controls.length === 0 ? (
                    <tr><td colSpan={4} style={{ textAlign: 'center', color: '#94a3b8' }}>No controls recorded</td></tr>
                  ) : fw.controls.map((ctrl, ci) => (
                    <tr key={ci}>
                      <td>
                        {ctrl.control_id && <span style={{ color: '#64748b', fontFamily: 'monospace', fontSize: 11, marginRight: 4 }}>{ctrl.control_id}</span>}
                        {ctrl.control_name}
                      </td>
                      <td>
                        <span style={{
                          display: 'inline-block', padding: '2px 10px', borderRadius: 12,
                          fontWeight: 600, fontSize: 12,
                          background: statusBg(ctrl.status), color: statusColor(ctrl.status),
                        }}>
                          {ctrl.status?.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ fontSize: 12, color: '#475569' }}>{ctrl.evidence || ctrl.finding || '—'}</td>
                      <td style={{ fontSize: 12, color: '#0D9488' }}>{ctrl.recommendation || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}

          {/* Data Residency */}
          <h3>Data Residency</h3>
          <p style={{ fontSize: 13 }}>
            <span style={{
              display: 'inline-block', padding: '2px 10px', borderRadius: 12, fontWeight: 600, fontSize: 12,
              background: data_residency?.verified ? '#dcfce7' : '#fee2e2',
              color: data_residency?.verified ? '#166534' : '#991b1b',
              marginRight: 8,
            }}>
              {data_residency?.verified ? 'UAE COMPLIANT' : 'NOT VERIFIED'}
            </span>
            {data_residency?.details?.finding && (
              <span style={{ color: '#475569' }}>{data_residency.details.finding}</span>
            )}
          </p>

          <div className="footer">
            DESC Compliance Audit Report | AI Smart Sourcing | Powered by &sigma;I | {formatDate(audit_date)} | Confidential
          </div>
        </div>

        {/* ===== PAGE 3: REMEDIATION & CERTIFICATION ===== */}
        <div className="report-page">
          <h2>Remediation &amp; Certification</h2>

          {remediation_items.length > 0 ? (
            <>
              <h3>Remediation Recommendations</h3>
              <table className="remediation-table">
                <thead>
                  <tr>
                    <th>Framework</th>
                    <th>Control</th>
                    <th>Recommendation</th>
                    <th>Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {remediation_items.map((item, i) => (
                    <tr key={i}>
                      <td>{item.framework}</td>
                      <td>
                        {item.control_id && <span style={{ fontFamily: 'monospace', fontSize: 11, marginRight: 4 }}>{item.control_id}</span>}
                        {item.control_name}
                      </td>
                      <td style={{ fontSize: 12 }}>{item.recommendation}</td>
                      <td><span className={`priority-${item.priority}`}>{item.priority?.toUpperCase()}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <div style={{ background: '#dcfce7', border: '1px solid #86efac', borderRadius: 8, padding: 16, margin: '16px 0', textAlign: 'center' }}>
              <p style={{ color: '#166534', fontWeight: 600, fontSize: 15, margin: 0 }}>
                This proposal meets DESC compliance requirements.
              </p>
              <p style={{ color: '#15803d', fontSize: 13, margin: '4px 0 0' }}>
                All assessed controls have passed or are within acceptable thresholds.
              </p>
            </div>
          )}

          {/* DESC AI Security Lifecycle */}
          <h3>DESC AI Security Lifecycle</h3>
          <div className="lifecycle-row">
            {(lifecycle_phases || []).map((p, i) => (
              <div
                key={i}
                className="lifecycle-item"
                style={{
                  background: p.status === 'pass' ? '#f0fdf4' : p.status === 'warning' ? '#fefce8' : '#fef2f2',
                  borderColor: p.status === 'pass' ? '#86efac' : p.status === 'warning' ? '#fde047' : '#fca5a5',
                }}
              >
                <div className="phase-name">{p.phase}</div>
                <div className="phase-status">
                  {p.status === 'pass' ? '✓' : p.status === 'warning' ? '!' : '✗'}
                </div>
                <div style={{ fontSize: 10, color: statusColor(p.status), fontWeight: 600 }}>
                  {p.status?.toUpperCase()}
                </div>
              </div>
            ))}
          </div>

          {/* Signature */}
          <div style={{ marginTop: 32, borderTop: '2px solid #0D9488', paddingTop: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
              <div>
                <p style={{ fontSize: 14, fontWeight: 600, color: '#0D9488', margin: '0 0 4px' }}>
                  Audited by AI Smart Sourcing &mdash; &sigma;I
                </p>
                <p style={{ fontSize: 12, color: '#64748b', margin: 0 }}>
                  Date: {formatDate(audit_date)} &nbsp;|&nbsp; Audit ID: {audit_id}
                </p>
                {hash_chain_signature && (
                  <p style={{ fontSize: 11, color: '#94a3b8', margin: '4px 0 0', fontFamily: 'monospace' }}>
                    Hash: {hash_chain_signature.slice(0, 32)}...
                  </p>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ width: 180, borderBottom: '1px solid #334155', marginBottom: 4 }}>&nbsp;</div>
                <p style={{ fontSize: 11, color: '#64748b', margin: 0 }}>Authorized Signature</p>
              </div>
            </div>
          </div>

          <div className="footer" style={{ marginTop: 32 }}>
            This report was generated by AI with human oversight. All findings are traceable to source evidence.
            <br />
            DESC Compliance Audit Report | AI Smart Sourcing | Powered by &sigma;I | Confidential
          </div>
        </div>
      </div>
    </>
  );
}
