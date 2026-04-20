import React, { useEffect, useState } from 'react';
import api from '../lib/api';

function formatDate(iso) {
  if (!iso) return 'N/A';
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'long', year: 'numeric',
    });
  } catch { return iso; }
}

function formatScore(val) {
  if (val == null) return 'N/A';
  return Number(val).toFixed(1);
}

export default function BoardBrief() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get('/api/v1/reports/board-brief/data')
      .then(res => setData(res.data))
      .catch(err => setError(err?.friendly?.message || 'Board Brief data is being prepared.'))
      .finally(() => setLoading(false));
  }, []);

  const handlePrint = () => window.print();

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#fff' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: 48, height: 48, border: '4px solid #e5e7eb', borderTopColor: '#0D9488', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
          <p style={{ color: '#6b7280' }}>Preparing Executive Board Brief...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#fff' }}>
        <div style={{ maxWidth: 520, textAlign: 'center', padding: 32, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12 }}>
          <p style={{ fontSize: 18, fontWeight: 600, color: '#0f172a', marginBottom: 8 }}>Board Brief Not Ready</p>
          <p style={{ color: '#475569' }}>{typeof error === 'string' ? error : 'Board Brief data is being prepared.'}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { summary, impact, top_proposals, compliance_concerns, sector_breakdown, shield, model_usage, recommendations, innovation_pipeline, pilot_performance, ecosystem_health } = data;

  return (
    <>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @media print {
          .no-print { display: none !important; }
          body { margin: 0; padding: 0; background: #fff !important; }
          @page { margin: 18mm 14mm; }
          .brief-page { page-break-after: always; }
          .brief-page:last-child { page-break-after: auto; }
          .brief-container { padding: 0 !important; }
        }
        .brief-container {
          max-width: 900px; margin: 0 auto; padding: 32px 24px;
          font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
          color: #1e293b; background: #fff; line-height: 1.5;
        }
        .brief-container h1 { font-size: 26px; font-weight: 700; color: #0D9488; margin: 0 0 4px; }
        .brief-container h2 { font-size: 18px; font-weight: 700; color: #0D9488; margin: 24px 0 12px; border-bottom: 2px solid #0D9488; padding-bottom: 4px; }
        .brief-container h3 { font-size: 15px; font-weight: 600; color: #334155; margin: 16px 0 8px; }
        .metrics-row { display: flex; gap: 16px; margin: 16px 0; }
        .metric-card {
          flex: 1; background: #f0fdfa; border: 1px solid #99f6e4; border-radius: 8px;
          padding: 14px; text-align: center;
        }
        .metric-card .value { font-size: 28px; font-weight: 700; color: #0D9488; }
        .metric-card .label { font-size: 12px; color: #64748b; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
        .impact-row { display: flex; gap: 12px; margin: 12px 0; }
        .impact-item {
          flex: 1; background: #fef3c7; border: 1px solid #fcd34d; border-radius: 8px;
          padding: 12px; text-align: center;
        }
        .impact-item .value { font-size: 22px; font-weight: 700; color: #92400e; }
        .impact-item .label { font-size: 11px; color: #78716c; margin-top: 2px; }
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
        .risk-bar { display: flex; height: 20px; border-radius: 4px; overflow: hidden; margin: 8px 0; }
        .risk-low { background: #22c55e; }
        .risk-medium { background: #eab308; }
        .risk-high { background: #ef4444; }
        .subtitle { font-size: 14px; color: #64748b; margin: 0 0 4px; }
        .date-line { font-size: 12px; color: #94a3b8; margin-bottom: 20px; }
        .pill { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 4px; }
        .gap-positive { color: #dc2626; font-weight: 600; }
        .gap-negative { color: #16a34a; font-weight: 600; }
        .gap-zero { color: #64748b; font-weight: 600; }
        .stat-highlight {
          display: inline-block; background: #0D9488; color: #fff; font-size: 22px;
          font-weight: 700; padding: 6px 18px; border-radius: 8px; margin-right: 12px;
        }
        .stat-label-inline { font-size: 13px; color: #64748b; }
        .bar-container { display: flex; height: 24px; border-radius: 6px; overflow: hidden; margin: 8px 0; background: #e5e7eb; }
        .bar-fill { display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; color: #fff; min-width: 24px; }
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

      <div className="brief-container">
        {/* ===== PAGE 1: EXECUTIVE SUMMARY ===== */}
        <div className="brief-page">
          <h1>AI Smart Sourcing — Executive Board Brief</h1>
          <p className="subtitle">Dubai Chambers | Prepared by Tamer Momtaz | &sigma;I Technology</p>
          <p className="date-line">
            Generated: {formatDate(data.generated_at)} &nbsp;|&nbsp;
            Period: {formatDate(data.period?.from)} — {formatDate(data.period?.to)}
          </p>

          {/* Headline Metrics */}
          <div className="metrics-row">
            <div className="metric-card">
              <div className="value">{summary.total_proposals}</div>
              <div className="label">Proposals Received</div>
            </div>
            <div className="metric-card">
              <div className="value">{summary.evaluated}</div>
              <div className="label">Evaluated</div>
            </div>
            <div className="metric-card">
              <div className="value">{summary.compliance_audits}</div>
              <div className="label">Compliance Audits</div>
            </div>
            <div className="metric-card">
              <div className="value">{formatScore(summary.avg_score)}</div>
              <div className="label">Avg Score</div>
            </div>
          </div>

          {/* Impact Meter */}
          <h2>Impact Summary</h2>
          <div className="impact-row">
            <div className="impact-item">
              <div className="value">{impact.hours_saved}h</div>
              <div className="label">Analyst Hours Saved</div>
            </div>
            <div className="impact-item">
              <div className="value">{impact.speed_multiplier}x</div>
              <div className="label">Speed Multiplier</div>
            </div>
            <div className="impact-item">
              <div className="value">${impact.total_cost_usd}</div>
              <div className="label">Total AI Cost</div>
            </div>
          </div>

          {/* Top Proposals */}
          <h2>Top Scored Proposals</h2>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Proposal</th>
                <th>Sector</th>
                <th>Composite Score</th>
                <th>Compliance</th>
              </tr>
            </thead>
            <tbody>
              {top_proposals.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: '#94a3b8' }}>No evaluated proposals yet</td></tr>
              ) : top_proposals.map((p, i) => (
                <tr key={i}>
                  <td>{i + 1}</td>
                  <td style={{ fontWeight: 500 }}>{p.title}</td>
                  <td>{p.sector || '—'}</td>
                  <td>
                    <span className={`score-badge ${p.composite_score >= 80 ? 'score-high' : p.composite_score >= 60 ? 'score-mid' : 'score-low'}`}>
                      {formatScore(p.composite_score)}
                    </span>
                  </td>
                  <td>{formatScore(p.compliance_score)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Compliance Concerns */}
          <h2>Top Compliance Concerns</h2>
          <table>
            <thead>
              <tr>
                <th>Proposal</th>
                <th>Sector</th>
                <th>Compliance Score</th>
              </tr>
            </thead>
            <tbody>
              {compliance_concerns.length === 0 ? (
                <tr><td colSpan={3} style={{ textAlign: 'center', color: '#94a3b8' }}>No compliance concerns</td></tr>
              ) : compliance_concerns.map((p, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{p.title}</td>
                  <td>{p.sector || '—'}</td>
                  <td>
                    <span className={`score-badge ${p.compliance_score >= 80 ? 'score-high' : p.compliance_score >= 60 ? 'score-mid' : 'score-low'}`}>
                      {formatScore(p.compliance_score)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="footer">
            Generated by AI Smart Sourcing | Tamer Momtaz | Powered by &sigma;I | {formatDate(data.generated_at)} | Confidential
          </div>
        </div>

        {/* ===== PAGE 2: SECTOR INTELLIGENCE ===== */}
        <div className="brief-page">
          <h2>Sector Intelligence</h2>

          <h3>Proposals by Sector</h3>
          <table>
            <thead>
              <tr>
                <th>Sector</th>
                <th>Count</th>
                <th>Avg Score</th>
              </tr>
            </thead>
            <tbody>
              {sector_breakdown.length === 0 ? (
                <tr><td colSpan={3} style={{ textAlign: 'center', color: '#94a3b8' }}>No sector data available</td></tr>
              ) : sector_breakdown.map((s, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{s.sector}</td>
                  <td>{s.count}</td>
                  <td>
                    <span className={`score-badge ${s.avg_score >= 80 ? 'score-high' : s.avg_score >= 60 ? 'score-mid' : 'score-low'}`}>
                      {formatScore(s.avg_score)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3>Compliance Posture Overview</h3>
          <div style={{ display: 'flex', gap: 24, margin: '12px 0' }}>
            <div>
              <span style={{ fontSize: 13, color: '#64748b' }}>Total Audits Completed: </span>
              <strong>{summary.compliance_audits}</strong>
            </div>
            <div>
              <span style={{ fontSize: 13, color: '#64748b' }}>Trend Reports Generated: </span>
              <strong>{summary.trend_reports}</strong>
            </div>
          </div>

          <h3>Evidence Validation Status</h3>
          <div style={{ display: 'flex', gap: 24, margin: '8px 0', fontSize: 13 }}>
            <div>Avg Evidence Grounding Score: <strong style={{ color: '#0D9488' }}>{formatScore(shield.avg_grounding)}%</strong></div>
            <div>Total Checks: <strong>{shield.total_checks}</strong></div>
          </div>
          {shield.total_checks > 0 && (
            <>
              <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>Risk Distribution</div>
              <div className="risk-bar">
                {shield.risk_distribution.low > 0 && (
                  <div className="risk-low" style={{ flex: shield.risk_distribution.low }} title={`Low: ${shield.risk_distribution.low}`} />
                )}
                {shield.risk_distribution.medium > 0 && (
                  <div className="risk-medium" style={{ flex: shield.risk_distribution.medium }} title={`Medium: ${shield.risk_distribution.medium}`} />
                )}
                {shield.risk_distribution.high > 0 && (
                  <div className="risk-high" style={{ flex: shield.risk_distribution.high }} title={`High: ${shield.risk_distribution.high}`} />
                )}
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: 11, color: '#64748b' }}>
                <span><span style={{ display: 'inline-block', width: 10, height: 10, background: '#22c55e', borderRadius: 2, marginRight: 4 }} />Low: {shield.risk_distribution.low}</span>
                <span><span style={{ display: 'inline-block', width: 10, height: 10, background: '#eab308', borderRadius: 2, marginRight: 4 }} />Medium: {shield.risk_distribution.medium}</span>
                <span><span style={{ display: 'inline-block', width: 10, height: 10, background: '#ef4444', borderRadius: 2, marginRight: 4 }} />High: {shield.risk_distribution.high}</span>
              </div>
            </>
          )}

          <div className="footer">
            Generated by AI Smart Sourcing | Tamer Momtaz | Powered by &sigma;I | {formatDate(data.generated_at)} | Confidential
          </div>
        </div>

        {/* ===== PAGE 3: AI OPERATIONS & TRANSPARENCY ===== */}
        <div className="brief-page">
          <h2>AI Operations & Transparency</h2>

          <h3>&sigma;I Intelligence Summary</h3>
          <div className="metrics-row">
            <div className="metric-card">
              <div className="value">{impact.total_iu}</div>
              <div className="label">Intelligence Units</div>
            </div>
            <div className="metric-card">
              <div className="value">${impact.total_cost_usd}</div>
              <div className="label">Total Cost</div>
            </div>
            <div className="metric-card">
              <div className="value">{impact.energy_kwh}</div>
              <div className="label">Energy (kWh)</div>
            </div>
            <div className="metric-card">
              <div className="value">{impact.operations}</div>
              <div className="label">AI Operations</div>
            </div>
          </div>

          <h3>Model Usage Breakdown</h3>
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Operations</th>
                <th>Share</th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(model_usage || {}).length === 0 ? (
                <tr><td colSpan={3} style={{ textAlign: 'center', color: '#94a3b8' }}>No model data available</td></tr>
              ) : Object.entries(model_usage).sort((a, b) => b[1] - a[1]).map(([model, count], i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{model}</td>
                  <td>{count}</td>
                  <td>{impact.operations > 0 ? ((count / impact.operations) * 100).toFixed(1) : 0}%</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3>Recommended for Pilot Phase</h3>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Proposal</th>
                <th>Sector</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {(recommendations || []).length === 0 ? (
                <tr><td colSpan={4} style={{ textAlign: 'center', color: '#94a3b8' }}>No recommendations yet</td></tr>
              ) : recommendations.map((p, i) => (
                <tr key={i}>
                  <td>{i + 1}</td>
                  <td style={{ fontWeight: 500 }}>{p.title}</td>
                  <td>{p.sector || '—'}</td>
                  <td>
                    <span className={`score-badge ${p.composite_score >= 80 ? 'score-high' : p.composite_score >= 60 ? 'score-mid' : 'score-low'}`}>
                      {formatScore(p.composite_score)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="footer">
            Generated by AI Smart Sourcing | Tamer Momtaz | Powered by &sigma;I | {formatDate(data.generated_at)} | Confidential
          </div>
        </div>

        {/* ===== PAGE 4: ECOSYSTEM INTELLIGENCE ===== */}
        <div className="brief-page">
          <h2>Ecosystem Intelligence</h2>

          {/* Innovation Pipeline */}
          <h3>Innovation Pipeline — Active Sourcing Cases</h3>
          <div style={{ display: 'flex', gap: 16, margin: '12px 0', flexWrap: 'wrap' }}>
            <div className="metric-card" style={{ flex: '0 0 auto', minWidth: 140 }}>
              <div className="value">{innovation_pipeline?.active_sourcing_cases ?? 0}</div>
              <div className="label">Active Cases</div>
            </div>
            <div className="metric-card" style={{ flex: '0 0 auto', minWidth: 140 }}>
              <div className="value">{innovation_pipeline?.total_sourcing_cases ?? 0}</div>
              <div className="label">Total Cases</div>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>Sector</th>
                <th>Active Cases</th>
              </tr>
            </thead>
            <tbody>
              {(innovation_pipeline?.sector_breakdown || []).length === 0 ? (
                <tr><td colSpan={2} style={{ textAlign: 'center', color: '#94a3b8' }}>No active sourcing cases</td></tr>
              ) : innovation_pipeline.sector_breakdown.map((s, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{s.sector}</td>
                  <td>{s.active_cases}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pilot Performance */}
          <h3>Pilot Performance</h3>
          <div className="metrics-row">
            <div className="metric-card">
              <div className="value">{pilot_performance?.total_pilots ?? 0}</div>
              <div className="label">Total Pilots</div>
            </div>
            <div className="metric-card">
              <div className="value">{pilot_performance?.active_pilots ?? 0}</div>
              <div className="label">Active</div>
            </div>
            <div className="metric-card">
              <div className="value">{pilot_performance?.completed_pilots ?? 0}</div>
              <div className="label">Completed</div>
            </div>
            <div className="metric-card">
              <div className="value">{pilot_performance?.success_rate ?? 0}%</div>
              <div className="label">Success Rate</div>
            </div>
            <div className="metric-card">
              <div className="value">{pilot_performance?.adoption_rate ?? 0}%</div>
              <div className="label">Adoption Rate</div>
            </div>
          </div>
          {pilot_performance?.avg_case_to_pilot_days != null && (
            <div style={{ margin: '8px 0', fontSize: 13, color: '#334155' }}>
              Avg time from sourcing case to pilot completion: <strong style={{ color: '#0D9488' }}>{pilot_performance.avg_case_to_pilot_days} days</strong>
            </div>
          )}

          {(pilot_performance?.top_vendors || []).length > 0 && (
            <>
              <h3>Top Vendors by Successful Pilots</h3>
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Vendor</th>
                    <th>Successful Pilots</th>
                  </tr>
                </thead>
                <tbody>
                  {pilot_performance.top_vendors.map((v, i) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td style={{ fontWeight: 500 }}>{v.vendor_name}</td>
                      <td>{v.successful_pilots}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {/* Ecosystem Health */}
          <h3>Ecosystem Health — Demand vs Supply by Sector</h3>
          <table>
            <thead>
              <tr>
                <th>Sector</th>
                <th>Demand (Cases)</th>
                <th>Supply (Proposals)</th>
                <th>Gap</th>
              </tr>
            </thead>
            <tbody>
              {(ecosystem_health || []).length === 0 ? (
                <tr><td colSpan={4} style={{ textAlign: 'center', color: '#94a3b8' }}>No ecosystem data available</td></tr>
              ) : ecosystem_health.map((e, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{e.sector}</td>
                  <td>{e.demand}</td>
                  <td>{e.supply}</td>
                  <td>
                    <span className={e.gap > 0 ? 'gap-positive' : e.gap < 0 ? 'gap-negative' : 'gap-zero'}>
                      {e.gap > 0 ? `+${e.gap} undersupplied` : e.gap < 0 ? `${Math.abs(e.gap)} oversupplied` : 'Balanced'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="footer">
            Generated by AI Smart Sourcing | Tamer Momtaz | Powered by &sigma;I | {formatDate(data.generated_at)} | Confidential
          </div>
        </div>
      </div>
    </>
  );
}
