import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import api from '../lib/api';

const STAGES = [
  { id: 0, name: 'Welcome', sidebar: null },
  { id: 1, name: 'Submit a Proposal', sidebar: 'Proposals' },
  { id: 2, name: 'AI Evaluation', sidebar: 'Evaluations' },
  { id: 3, name: 'Hallucination Shield', sidebar: 'Evaluations' },
  { id: 4, name: 'DESC Compliance', sidebar: 'Compliance Audits' },
  { id: 5, name: 'Market Intelligence', sidebar: 'Trend Analyses' },
  { id: 6, name: 'Compare Proposals', sidebar: 'Compare' },
  { id: 7, name: 'Dashboard', sidebar: 'Dashboard' },
  { id: 8, name: 'Vendors', sidebar: 'Vendors' },
  { id: 9, name: 'Documents', sidebar: 'Documents' },
  { id: 10, name: 'Business Groups', sidebar: 'Business Groups' },
  { id: 11, name: 'Users', sidebar: 'Users' },
  { id: 12, name: 'σI Transparency', sidebar: 'ΣI Transparency' },
  { id: 13, name: 'Vendor Intelligence — vScore', sidebar: 'Vendor Intelligence' },
  { id: 14, name: 'Finale', sidebar: null },
];

const TOOLTIPS = {
  1: 'Proposals — submit via PDF upload or manual form',
  2: 'Evaluations — AI-powered scoring with full reasoning',
  3: 'Evaluations — Shield verification inside each evaluation',
  4: 'Compliance Audits — automated DESC framework assessment',
  5: 'Trend Analyses — on-demand market intelligence with PDF export',
  6: 'Compare — side-by-side decision-making tool',
  7: 'Dashboard — live metrics with Impact Meter and Board Brief',
  8: 'Vendors — profiles with DESC certification status',
  9: 'Documents — source of truth powering AI accuracy',
  10: 'Business Groups — sector-specific evaluation configuration',
  11: 'Users — role-based access management',
  12: 'ΣI Transparency — full AI cost and environmental accountability',
  13: 'Vendor Intelligence — supplier credit scoring with vScore',
};

/* ─── Particle Field ─── */
function ParticleField() {
  const particles = useMemo(() => {
    return Array.from({ length: 60 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      size: 1 + Math.random() * 2,
      opacity: 0.15 + Math.random() * 0.35,
      duration: 15 + Math.random() * 25,
      delay: -(Math.random() * 40),
      z: -100 + Math.random() * 200,
    }));
  }, []);

  return (
    <div style={{
      position: 'absolute', inset: 0, overflow: 'hidden',
      perspective: '600px', zIndex: 1
    }}>
      {particles.map(p => (
        <div key={p.id} style={{
          position: 'absolute',
          left: `${p.left}%`,
          bottom: '-5%',
          width: `${p.size}px`,
          height: `${p.size}px`,
          borderRadius: '50%',
          background: `rgba(255,255,255,${p.opacity})`,
          animation: `particleDrift ${p.duration}s linear infinite`,
          animationDelay: `${p.delay}s`,
          transform: `translateZ(${p.z}px)`,
        }} />
      ))}
    </div>
  );
}

/* ─── Hero Section (Stage 0) ─── */
function HeroSection({ onStart, impact, session }) {
  const [phase, setPhase] = useState(0);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  useEffect(() => {
    if (reducedMotion) {
      setPhase(5);
      return;
    }
    const timers = [
      setTimeout(() => setPhase(1), 1500),
      setTimeout(() => setPhase(2), 3500),
      setTimeout(() => setPhase(3), 5000),
      setTimeout(() => setPhase(4), 7000),
      setTimeout(() => setPhase(5), 9000),
    ];
    return () => timers.forEach(clearTimeout);
  }, [reducedMotion]);

  const show = (minPhase) => reducedMotion || phase >= minPhase;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: '#0F172A', minHeight: '100vh', display: 'flex',
      flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      overflow: 'hidden', zIndex: 50
    }}>
      <ParticleField />

      <div style={{ position: 'relative', zIndex: 2, textAlign: 'center' }}>
        {/* "AI Smart Sourcing" */}
        <h1 style={{
          fontSize: '42px', fontWeight: 500, color: '#fff',
          letterSpacing: '2px', marginBottom: '16px',
          opacity: show(1) ? 1 : 0,
          transform: show(1) ? 'scale(1)' : 'scale(0.95)',
          transition: 'opacity 2s ease-out, transform 2s ease-out'
        }}>
          AI Smart Sourcing
        </h1>

        {/* "powered by σI" */}
        <div style={{
          fontSize: '18px', color: '#94A3B8', marginBottom: '24px',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
        }}>
          <span style={{
            opacity: show(2) ? 1 : 0,
            transition: 'opacity 1s ease-out'
          }}>powered by</span>
          <span style={{
            fontSize: '28px', fontWeight: 700, color: '#0D9488',
            opacity: show(3) ? 1 : 0,
            transform: show(3) ? 'translateX(0)' : 'translateX(120px)',
            transition: 'opacity 0.8s ease-out, transform 2s cubic-bezier(0.16, 1, 0.3, 1)'
          }}>σI</span>
        </div>

        {/* Subtitle */}
        <p style={{
          fontSize: '14px', color: '#64748B', marginBottom: '40px',
          opacity: show(4) ? 1 : 0,
          transition: 'opacity 1s ease-out'
        }}>
          Dubai Chambers | by Tamer Momtaz
        </p>

        {/* Live stats */}
        {show(5) && impact && (
          <div style={{
            display: 'flex', gap: '24px', justifyContent: 'center',
            marginBottom: '32px', fontSize: '13px', color: '#64748B',
            opacity: show(5) ? 1 : 0, transition: 'opacity 1s ease-out',
            flexWrap: 'wrap'
          }}>
            <span><span style={{ color: '#0D9488', fontFamily: 'monospace' }}>{impact.summary?.total_proposals || '—'}</span> proposals processed</span>
            <span><span style={{ color: '#0D9488', fontFamily: 'monospace' }}>{impact.time_saved?.total_hours || '—'}</span> analyst-hours saved</span>
            <span><span style={{ color: '#0D9488', fontFamily: 'monospace' }}>${impact.ai_performance?.total_cost_usd || '—'}</span> total AI cost</span>
          </div>
        )}

        {/* CTA button */}
        {show(5) && (
          <div style={{ opacity: show(5) ? 1 : 0, transition: 'opacity 1s ease-out' }}>
            <button onClick={onStart} style={{
              background: 'transparent', border: '1.5px solid #0D9488',
              color: '#0D9488', padding: '14px 40px', borderRadius: '8px',
              fontSize: '16px', cursor: 'pointer', letterSpacing: '0.5px',
              transition: 'background 0.3s, color 0.3s'
            }}
            onMouseEnter={e => { e.target.style.background = '#0D9488'; e.target.style.color = '#fff'; }}
            onMouseLeave={e => { e.target.style.background = 'transparent'; e.target.style.color = '#0D9488'; }}
            >
              Explore the platform →
            </button>
            {!session && (
              <p style={{ marginTop: '16px', fontSize: '13px', color: '#64748B' }}>
                <a href="/login" style={{ color: '#0D9488', textDecoration: 'none' }}>
                  Sign in to explore the full platform
                </a>
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Stage Content (all 12 stages) ─── */
const STAGE_CONTENT = {
  1: {
    title: "Submit a proposal",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          Vendors can <strong style={{color:'#0F172A'}}>upload a PDF</strong> and
          AI extracts everything automatically — company info, technology type,
          sector, and maturity level. Or they can{' '}
          <strong style={{color:'#0F172A'}}>fill in the details manually</strong> using
          the submission form.
        </p>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '24px' }}>
          Vendor records are auto-created on first submission. Business group
          auto-assigned based on sector.
        </p>
        {/* Visual: animated tags */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {['Cybersecurity', 'Production', 'Dubai', 'DESC Certified'].map((tag, i) => (
            <span key={tag} style={{
              background: 'rgba(13,148,136,0.15)', color: '#0D9488',
              padding: '6px 14px', borderRadius: '20px', fontSize: '13px',
              animation: `slideUp 0.5s ease-out ${0.3 * i}s both`
            }}>{tag}</span>
          ))}
        </div>
      </div>
    )
  },

  2: {
    title: "AI evaluation — multi-model scoring",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          Each proposal is scored across 4 dimensions{' '}
          <strong style={{color:'#0F172A'}}>in seconds</strong> — not hours, not days.
          Multi-model AI (Claude, GPT-4o, Gemini) ensures no single-model bias.
          Full reasoning is provided for every score.
        </p>
        {/* Visual: score bars */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {[
            { label: 'Relevance', score: 92 },
            { label: 'Feasibility', score: 88 },
            { label: 'Sector Alignment', score: 95 },
            { label: 'Compliance', score: 94 },
          ].map((dim, i) => (
            <div key={dim.label} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ width: '120px', fontSize: '13px', color: '#475569' }}>{dim.label}</span>
              <div style={{ flex: 1, height: '6px', borderRadius: '3px', background: '#E2E8F0' }}>
                <div style={{
                  height: '100%', borderRadius: '3px', background: '#0D9488',
                  width: `${dim.score}%`,
                  animation: `barFill 1.5s ease-out ${0.3 * i}s both`
                }} />
              </div>
              <span style={{ width: '32px', fontSize: '14px', color: '#0D9488', fontWeight: 500, textAlign: 'right' }}>
                {dim.score}
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  },

  3: {
    title: "Hallucination Shield — can you trust the AI?",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          After every evaluation, a <strong style={{color:'#0F172A'}}>second AI pass</strong> verifies
          every factual claim against the source document. A{' '}
          <strong style={{color:'#0F172A'}}>different AI model</strong> independently
          re-scores to detect anomalies. Claims are classified as:
        </p>
        {/* Visual: claim types */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {[
            { icon: 'G', color: '#0D9488', bg: 'rgba(13,148,136,0.15)', text: 'Grounded — claim directly supported by proposal text' },
            { icon: 'P', color: '#BA7517', bg: 'rgba(186,117,23,0.15)', text: 'Partial — related content exists but claim is extrapolated' },
            { icon: 'U', color: '#A32D2D', bg: 'rgba(163,45,45,0.15)', text: 'Ungrounded — no supporting text found in the source' },
          ].map((claim, i) => (
            <div key={claim.icon} style={{
              display: 'flex', alignItems: 'center', gap: '12px',
              animation: `slideUp 0.5s ease-out ${0.4 * i}s both`
            }}>
              <div style={{
                width: '28px', height: '28px', borderRadius: '50%',
                background: claim.bg, color: claim.color,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '12px', fontWeight: 600, flexShrink: 0
              }}>{claim.icon}</div>
              <span style={{ fontSize: '13px', color: '#475569' }}>{claim.text}</span>
            </div>
          ))}
        </div>
      </div>
    )
  },

  4: {
    title: "DESC compliance — automated",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          Automated review against three DESC frameworks: ISR V3, AI Security
          Policy (covering the full lifecycle: design, develop, deploy, monitor,
          dispose), and Cloud Service Provider Standards.
        </p>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '24px' }}>
          Each control is checked individually with pass, fail, or warning status
          and supporting evidence. Data residency violations are flagged automatically.
        </p>
        {/* Visual: framework badges */}
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {[
            { name: 'ISR V3', status: 'Pass', color: '#0D9488', bg: 'rgba(13,148,136,0.15)' },
            { name: 'AI Security', status: 'Pass', color: '#0D9488', bg: 'rgba(13,148,136,0.15)' },
            { name: 'CSP', status: 'Warning', color: '#BA7517', bg: 'rgba(186,117,23,0.15)' },
          ].map((fw, i) => (
            <div key={fw.name} style={{
              padding: '10px 20px', borderRadius: '8px', background: fw.bg,
              animation: `slideUp 0.5s ease-out ${0.5 * i}s both`
            }}>
              <span style={{ color: fw.color, fontSize: '14px', fontWeight: 500 }}>
                {fw.name}: {fw.status} {fw.status === 'Pass' ? '✓' : '⚠'}
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  },

  5: {
    title: "Market intelligence — generated on demand",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          From this page, you can <strong style={{color:'#0F172A'}}>generate AI-powered
          market intelligence reports</strong> covering any time period. The AI analyzes
          all evaluated proposals and produces sector breakdowns, technology trends,
          D33 alignment scores, and actionable recommendations.
        </p>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '24px' }}>
          Reports can be <strong style={{color:'#0F172A'}}>exported as professional PDFs</strong> —
          ready for board meetings. One click to generate, one click to export.
        </p>
        {/* Visual: mini report card */}
        <div style={{
          border: '1px solid rgba(13,148,136,0.3)', borderRadius: '8px',
          padding: '16px 20px', animation: 'slideUp 0.6s ease-out'
        }}>
          <div style={{ color: '#0F172A', fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>
            Smart Sourcing Report
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-tertiary)', lineHeight: 1.8 }}>
            Sector breakdown • D33 alignment • Technology trends • 8 recommendations
          </div>
          <div style={{
            marginTop: '12px', display: 'inline-block',
            padding: '4px 12px', borderRadius: '4px',
            background: 'rgba(13,148,136,0.15)', color: '#0D9488', fontSize: '12px'
          }}>
            Export PDF ↓
          </div>
        </div>
      </div>
    )
  },

  6: {
    title: "Compare proposals side by side",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          Select 2 or 3 proposals and compare everything in one view — evaluation
          scores, hallucination shield integrity, compliance status, and proposal
          details. The highest scorer per dimension is highlighted automatically.
        </p>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '24px' }}>
          The tool procurement officers actually need — no more switching between tabs.
        </p>
        {/* Visual: two mini columns */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div style={{
            border: '1px solid rgba(13,148,136,0.3)', borderRadius: '8px',
            padding: '14px', textAlign: 'center', animation: 'slideUp 0.5s ease-out'
          }}>
            <div style={{ fontSize: '13px', color: '#475569' }}>Proposal A</div>
            <div style={{ fontSize: '24px', fontWeight: 500, color: '#0D9488', marginTop: '4px' }}>92.3</div>
            <span style={{
              fontSize: '10px', background: 'rgba(13,148,136,0.15)',
              color: '#0D9488', padding: '2px 8px', borderRadius: '10px'
            }}>Best</span>
          </div>
          <div style={{
            border: '1px solid rgba(100,116,139,0.3)', borderRadius: '8px',
            padding: '14px', textAlign: 'center', animation: 'slideUp 0.5s ease-out 0.2s both'
          }}>
            <div style={{ fontSize: '13px', color: '#475569' }}>Proposal B</div>
            <div style={{ fontSize: '24px', fontWeight: 500, color: '#475569', marginTop: '4px' }}>91.5</div>
          </div>
        </div>
      </div>
    )
  },

  7: {
    title: "Your command center",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          The Dashboard shows <strong style={{color:'#0F172A'}}>live platform metrics</strong> —
          total proposals, evaluations completed, compliance audits, and average scores.
          All numbers update in real time as new proposals are processed.
        </p>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          At the top: the <strong style={{color:'#0F172A'}}>σI Impact Meter</strong> —
          a live Return on Time calculator showing analyst-hours saved, working days
          recovered, and total AI cost. With full methodology explaining every estimate.
        </p>
        <p style={{ color: '#475569', lineHeight: 1.7 }}>
          One click to generate the <strong style={{color:'#0F172A'}}>Executive Board
          Brief</strong> — a professional 3-page PDF report ready for leadership.
        </p>
      </div>
    )
  },

  8: {
    title: "Know your vendors",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          Every vendor who submits a proposal gets a profile — company details,
          country of origin, DESC certification status, and complete submission history.
        </p>
        <p style={{ color: '#475569', lineHeight: 1.7 }}>
          From this page, you can review vendor backgrounds before evaluating
          their proposals.
        </p>
      </div>
    )
  },

  9: {
    title: "Central document library",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          Every document uploaded with a proposal — PDFs, presentations,
          spreadsheets — lives here in one searchable library.
        </p>
        <p style={{ color: '#475569', lineHeight: 1.7 }}>
          <strong style={{color:'#0F172A'}}>Why this matters:</strong> the AI reads
          these documents during evaluation and the Hallucination Shield verifies
          claims against them. The richer the document, the more accurate the AI
          assessment. Documents are the source of truth.
        </p>
      </div>
    )
  },

  10: {
    title: "Organized by sector",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          From this page, you can <strong style={{color:'#0F172A'}}>view all sector
          groups</strong> and <strong style={{color:'#0F172A'}}>configure how each
          sector is evaluated</strong>. Different sectors have different priorities —
          a cybersecurity proposal should weigh compliance higher, while an AgTech
          proposal should weigh feasibility higher.
        </p>
        <p style={{ color: '#475569', lineHeight: 1.7 }}>
          Each group has its own evaluation weight configuration that shapes how
          the AI scores proposals in that sector.
        </p>
      </div>
    )
  },

  11: {
    title: "Role-based access",
    render: () => (
      <div>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
          From this page, you can manage platform users and assign roles.
          Different roles see different capabilities:
        </p>
        <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '24px' }}>
          Vendors submit proposals. Analysts run evaluations. Compliance Officers
          conduct audits. Executives access board briefs and trend reports. Each
          role sees only what they need.
        </p>
        {/* Visual: role badges */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {['Admin', 'Analyst', 'Compliance Officer', 'Vendor'].map((role, i) => (
            <span key={role} style={{
              padding: '6px 14px', borderRadius: '20px', fontSize: '13px',
              background: 'rgba(13,148,136,0.15)', color: '#0D9488',
              animation: `slideUp 0.5s ease-out ${0.2 * i}s both`
            }}>{role}</span>
          ))}
        </div>
      </div>
    )
  },

  12: {
    title: "σI Transparency",
    render: () => null // Handled by RevealSection in main render
  },

  13: {
    title: "Vendor Intelligence — vScore",
    render: () => {
      /* Animated vScore gauge count-up */
      const VScoreDemo = () => {
        const [val, setVal] = useState(300);
        useEffect(() => {
          const duration = 2000;
          const start = performance.now();
          const animate = (now) => {
            const pct = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - pct, 3); // ease-out cubic
            setVal(Math.round(300 + eased * 532));
            if (pct < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
        }, []);
        return (
          <div style={{
            width: '100px', height: '100px', borderRadius: '50%',
            border: '4px solid #0D9488', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            fontSize: '28px', fontWeight: 700, color: '#0D9488',
            margin: '0 auto 16px', animation: 'slideUp 0.6s ease-out'
          }}>
            {val}
          </div>
        );
      };

      return (
        <div>
          <VScoreDemo />
          <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
            Every vendor gets a vScore — a 300 to 900 credit score that tells
            you how much you can trust them. Like a financial credit bureau, but
            for suppliers. Platinum, Gold, Silver, Bronze, or Under Review.
          </p>
          <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '20px' }}>
            The vScore aggregates five dimensions: Performance History from past
            engagements, Proposal Quality from AI evaluations, Compliance from
            DESC and ISO certifications, Claim Integrity from the Hallucination
            Shield, and Entity Intelligence from related company analysis.
          </p>
          <p style={{ color: '#475569', lineHeight: 1.7, marginBottom: '24px' }}>
            Every score comes with an AI-generated risk narrative — a plain-English
            assessment that reads like a credit report. And because this is σI,
            every factor, every data point, every calculation is transparent and
            traceable.
          </p>

          {/* Tier badges appearing one by one */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
            {[
              { name: 'Platinum', color: '#0D9488' },
              { name: 'Gold', color: '#B8904A' },
              { name: 'Silver', color: '#3B82F6' },
              { name: 'Bronze', color: '#F59E0B' },
              { name: 'Under Review', color: '#EF4444' },
            ].map((tier, i) => (
              <span key={tier.name} style={{
                padding: '6px 14px', borderRadius: '20px', fontSize: '13px',
                background: `${tier.color}20`, color: tier.color, fontWeight: 600,
                animation: `slideUp 0.5s ease-out ${0.3 * i}s both`
              }}>{tier.name}</span>
            ))}
          </div>

          {/* Mini radar chart representation */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px',
            maxWidth: '400px'
          }}>
            {[
              { dim: 'Performance', pct: 85 },
              { dim: 'Quality', pct: 78 },
              { dim: 'Compliance', pct: 92 },
              { dim: 'Integrity', pct: 88 },
              { dim: 'Entity', pct: 72 },
            ].map((d, i) => (
              <div key={d.dim} style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                animation: `slideUp 0.5s ease-out ${0.2 * i + 1.5}s both`
              }}>
                <span style={{ width: '80px', fontSize: '12px', color: '#475569' }}>{d.dim}</span>
                <div style={{ flex: 1, height: '5px', borderRadius: '3px', background: '#E2E8F0' }}>
                  <div style={{
                    height: '100%', borderRadius: '3px', background: '#0D9488',
                    width: `${d.pct}%`,
                    animation: `barFill 1.5s ease-out ${0.2 * i + 1.5}s both`
                  }} />
                </div>
                <span style={{ width: '24px', fontSize: '11px', color: '#0D9488', fontWeight: 500, textAlign: 'right' }}>
                  {d.pct}
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }
  },
};

/* ─── Stage Card ─── */
function StageCard({ stage }) {
  // Each stage is a card with: number circle, title, description, visual element
  const content = STAGE_CONTENT[stage];
  if (!content) return null;

  return (
    <div key={stage} style={{
      maxWidth: '700px', width: '100%', padding: '40px',
      animation: 'slideUp 0.6s ease-out'
    }}>
      <div style={{
        width: '48px', height: '48px', borderRadius: '50%',
        background: '#0D9488', color: '#fff', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
        fontSize: '18px', fontWeight: 500, marginBottom: '20px'
      }}>
        {stage}
      </div>
      <h2 style={{ fontSize: '24px', fontWeight: 500, marginBottom: '12px', color: '#1E293B' }}>
        {content.title}
      </h2>
      {content.render()}
    </div>
  );
}

/* ─── Navigation Bar ─── */
function NavigationBar({ current, total, stageName, onNext, onBack, onJump, isLast }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '16px 24px', borderTop: '0.5px solid var(--color-border-tertiary, #E2E8F0)',
      background: 'var(--color-background-secondary, #F1F5F9)'
    }}>
      <button onClick={onBack} disabled={current <= 1}
        style={{
          background: 'none', border: 'none', color: current <= 1 ? 'var(--color-text-tertiary, #94A3B8)' : 'var(--color-text-secondary, #475569)',
          cursor: current <= 1 ? 'default' : 'pointer', fontSize: '14px', padding: '8px 16px'
        }}>
        ← Back
      </button>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {Array.from({ length: total }, (_, i) => (
          <div key={i + 1} onClick={() => onJump(i + 1)}
            style={{
              width: current === i + 1 ? '24px' : '8px',
              height: '8px',
              borderRadius: '4px',
              background: i + 1 <= current ? '#0D9488' : 'var(--color-border-tertiary, #CBD5E1)',
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
          />
        ))}
        <span style={{ color: 'var(--color-text-secondary, #64748B)', fontSize: '12px', marginLeft: '12px' }}>
          {current}/{total} — {stageName}
        </span>
      </div>

      <button onClick={onNext}
        style={{
          background: 'none', border: '1px solid #0D9488', color: '#0D9488',
          cursor: 'pointer', fontSize: '14px', padding: '8px 20px', borderRadius: '6px'
        }}>
        {isLast ? 'See the reveal →' : 'Next →'}
      </button>
    </div>
  );
}

/* ─── Reveal Section (Stage 12) ─── */
function RevealSection({ impact }) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 2000),
      setTimeout(() => setPhase(3), 5000),
      setTimeout(() => setPhase(4), 6500),
      setTimeout(() => setPhase(5), 8000),
    ];
    return () => timers.forEach(clearTimeout);
  }, []);

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const show = (minPhase) => reducedMotion || phase >= minPhase;

  const aiMinutes = impact?.ai_performance?.ai_minutes || '—';
  const hoursSaved = impact?.time_saved?.total_hours || '—';
  const totalCost = impact?.ai_performance?.total_cost_usd || '—';

  return (
    <div style={{ maxWidth: '600px', textAlign: 'center' }}>
      {/* Description */}
      <p style={{
        color: '#94A3B8', fontSize: '16px', lineHeight: 1.8, marginBottom: '40px',
        opacity: show(1) ? 1 : 0, transition: 'opacity 1s ease-out'
      }}>
        From this page, every single AI interaction is tracked — model used,
        tokens consumed, cost in dollars, energy in kilowatt-hours, and carbon footprint.
      </p>

      {/* σI Definition */}
      <div style={{
        marginBottom: '48px',
        opacity: show(2) ? 1 : 0,
        transition: 'opacity 1.5s ease-out'
      }}>
        <p style={{
          fontSize: '22px', fontWeight: 500, color: '#fff', marginBottom: '16px'
        }}>
          <span style={{ color: '#0D9488' }}>σI</span> — coined by Tee — stands for Added Intelligence.
        </p>
        <p style={{
          color: '#94A3B8', fontSize: '15px', lineHeight: 1.8, maxWidth: '500px', margin: '0 auto'
        }}>
          Not artificial. Not a replacement. Added. Intelligence that augments
          human judgment, with full transparency about what it costs, what it
          consumes, and what it claims.
        </p>
      </div>

      {/* Impact numbers */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
        <p style={{
          fontSize: '20px', color: '#e2e8f0', fontWeight: 500,
          opacity: show(3) ? 1 : 0,
          transform: show(3) ? 'translateY(0)' : 'translateY(10px)',
          transition: 'opacity 1s ease-out, transform 1s ease-out'
        }}>
          <span style={{ color: '#0D9488', fontFamily: 'monospace', fontSize: '24px' }}>{aiMinutes}</span> minutes of AI time.
        </p>

        <p style={{
          fontSize: '20px', color: '#e2e8f0', fontWeight: 500,
          opacity: show(4) ? 1 : 0,
          transform: show(4) ? 'translateY(0)' : 'translateY(10px)',
          transition: 'opacity 1s ease-out, transform 1s ease-out'
        }}>
          Replacing <span style={{ color: '#0D9488', fontFamily: 'monospace', fontSize: '24px' }}>{hoursSaved}</span> hours of manual analysis.
        </p>

        <p style={{
          fontSize: '20px', color: '#e2e8f0', fontWeight: 500,
          opacity: show(5) ? 1 : 0,
          transform: show(5) ? 'translateY(0)' : 'translateY(10px)',
          transition: 'opacity 1s ease-out, transform 1s ease-out'
        }}>
          At a total cost of <span style={{ color: '#0D9488', fontFamily: 'monospace', fontSize: '24px' }}>${totalCost}</span>.
        </p>
      </div>
    </div>
  );
}

/* ─── Finale Section ─── */
function FinaleSection({ impact, onReplay, onExplore, onBack }) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000),
      setTimeout(() => setPhase(2), 2500),
      setTimeout(() => setPhase(3), 4500),
    ];
    return () => timers.forEach(clearTimeout);
  }, []);

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const show = (minPhase) => reducedMotion || phase >= minPhase;

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      position: 'relative', zIndex: 2, textAlign: 'center', padding: '2rem'
    }}>
      {/* Slogan 1 */}
      <p style={{
        fontSize: '28px', fontWeight: 500, color: '#0D9488',
        marginBottom: '20px', letterSpacing: '1px',
        opacity: show(1) ? 1 : 0,
        transform: show(1) ? 'translateY(0)' : 'translateY(15px)',
        transition: 'opacity 1.5s ease-out, transform 1.5s ease-out'
      }}>
        For σI, AI means Added Intelligence.
      </p>

      {/* Slogan 2 */}
      <p style={{
        fontSize: '28px', fontWeight: 500, color: '#0D9488',
        marginBottom: '48px', letterSpacing: '1px',
        opacity: show(2) ? 1 : 0,
        transform: show(2) ? 'translateY(0)' : 'translateY(15px)',
        transition: 'opacity 1.5s ease-out, transform 1.5s ease-out'
      }}>
        AI means Awareness Implemented.
      </p>

      {/* Attribution + CTAs */}
      <div style={{
        opacity: show(3) ? 1 : 0,
        transition: 'opacity 1s ease-out'
      }}>
        <p style={{
          fontSize: '14px', color: '#64748B', marginBottom: '40px'
        }}>
          AI Smart Sourcing — Dubai Chambers | by Tamer Momtaz
        </p>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap', marginTop: '40px', position: 'relative', zIndex: 10 }}>
          <button onClick={onExplore} style={{
            background: '#0D9488', border: 'none', color: '#fff',
            padding: '12px 28px', borderRadius: '8px', fontSize: '14px',
            cursor: 'pointer'
          }}>
            Start exploring
          </button>

          <button onClick={() => window.open('/board-brief', '_blank')} style={{
            background: 'transparent', border: '1px solid #0D9488',
            color: '#0D9488', padding: '12px 28px', borderRadius: '8px',
            fontSize: '14px', cursor: 'pointer'
          }}>
            Board Brief
          </button>

          <button onClick={onReplay} style={{
            background: 'transparent', border: '1px solid #475569',
            color: '#94A3B8', padding: '12px 28px', borderRadius: '8px',
            fontSize: '14px', cursor: 'pointer'
          }}>
            Replay
          </button>

          <button onClick={onBack} style={{
            background: 'transparent', border: '1px solid #475569',
            color: '#94A3B8', padding: '12px 28px', borderRadius: '8px',
            fontSize: '14px', cursor: 'pointer'
          }}>
            ← Back
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── Main Component ─── */
export default function HowItWorks() {
  const [currentStage, setCurrentStage] = useState(0);
  const [impactData, setImpactData] = useState(null);
  const navigate = useNavigate();

  let session = null;
  try {
    const auth = useAuth();
    session = auth?.session ?? null;
  } catch {
    // Outside AuthProvider — public route
  }

  // Fetch live impact data for hero + finale
  useEffect(() => {
    api.get('/api/v1/dashboard/impact')
      .then(res => setImpactData(res.data))
      .catch(() => null);
  }, []);

  // Sidebar highlighting
  useEffect(() => {
    const stage = STAGES[currentStage];
    if (stage?.sidebar) {
      window.dispatchEvent(new CustomEvent('highlight-sidebar', {
        detail: { item: stage.sidebar, tooltip: TOOLTIPS[currentStage] || '' }
      }));
    }
    return () => {
      window.dispatchEvent(new CustomEvent('highlight-sidebar', {
        detail: { item: null, tooltip: '' }
      }));
    };
  }, [currentStage]);

  const next = () => setCurrentStage(prev => Math.min(prev + 1, 14));
  const back = () => setCurrentStage(prev => Math.max(prev - 1, 0));
  const jumpTo = (stage) => setCurrentStage(stage);
  const startJourney = () => { setCurrentStage(1); };

  // Render hero if stage 0
  if (currentStage === 0) {
    return <HeroSection onStart={startJourney} impact={impactData} session={session} />;
  }

  // Stage 12 gets the dark cinematic treatment (like the hero)
  if (currentStage === 12) {
    return (
      <div style={{ minHeight: 'calc(100vh - 64px)', background: '#0F172A', display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden' }}>
        <ParticleField />
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', zIndex: 2, padding: '2rem' }}>
          <RevealSection impact={impactData} />
        </div>
        <div style={{ position: 'relative', zIndex: 10, borderTop: '0.5px solid rgba(255,255,255,0.1)', background: 'rgba(15,23,42,0.8)' }}>
          <NavigationBar current={12} total={13} stageName="σI Transparency" onNext={next} onBack={back} onJump={jumpTo} isLast={false} />
        </div>
      </div>
    );
  }

  // Render finale if stage 14
  if (currentStage === 14) {
    return (
      <div style={{ minHeight: 'calc(100vh - 64px)', background: '#0F172A', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' }}>
        <ParticleField />
        <FinaleSection
          impact={impactData}
          onReplay={() => setCurrentStage(0)}
          onExplore={() => navigate('/dashboard')}
          onBack={() => setCurrentStage(13)}
        />
      </div>
    );
  }

  // Stages 1-11, 13: normal content cards
  return (
    <div style={{ minHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
        <StageCard stage={currentStage} />
      </div>
      <NavigationBar current={currentStage} total={13} stageName={STAGES[currentStage]?.name} onNext={next} onBack={back} onJump={jumpTo} isLast={currentStage === 13} />
    </div>
  );
}
