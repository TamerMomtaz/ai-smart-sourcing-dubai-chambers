import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import api from '../lib/api';
import LivePulseBanner from '../components/LivePulseBanner';

const STAGES = [
  { id: 0, name: 'Welcome', sidebar: null },
  { id: 1, name: 'The Problem', sidebar: null },
  { id: 2, name: 'Signal Received', sidebar: 'Proposals' },
  { id: 3, name: 'Case Structured', sidebar: 'Proposals' },
  { id: 4, name: 'Vendors Discovered', sidebar: 'Vendors' },
  { id: 5, name: 'Compliance Gate', sidebar: 'Compliance Audits' },
  { id: 6, name: 'AI Evaluation', sidebar: 'Evaluations' },
  { id: 7, name: 'Stage-Gate', sidebar: 'Compare' },
  { id: 8, name: 'Pilot Tracking', sidebar: 'Dashboard' },
  { id: 9, name: 'Compliance', sidebar: 'Compliance Audits' },
  { id: 10, name: 'Ecosystem Intelligence', sidebar: 'Dashboard' },
  { id: 11, name: 'σI Transparency', sidebar: 'ΣI Transparency' },
  { id: 12, name: 'About', sidebar: null },
  { id: 13, name: 'Finale', sidebar: null },
];

const TOOLTIPS = {
  2: 'Proposals — multi-channel intake from ecosystem partners',
  3: 'Proposals — AI extracts and classifies sourcing needs',
  4: 'Vendors — AI matches vendors to cases proactively',
  5: 'Compliance Audits — rule-based checks before AI evaluation',
  6: 'Evaluations — 5-dimension scoring with evidence attribution',
  7: 'Compare — GO/KILL/HOLD decisions by human committees',
  8: 'Dashboard — lifecycle from setup to measured outcomes',
  9: 'Compliance Audits — DESC, OWASP, Ethics, Audit Evidence Pack',
  10: 'Dashboard — Board Brief, KPIs, channel analytics',
  11: 'ΣI Transparency — full AI cost and environmental accountability',
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

        {/* Live Pulse stats */}
        {show(5) && (
          <div style={{
            marginBottom: '32px', maxWidth: '560px', width: '100%',
            opacity: show(5) ? 1 : 0, transition: 'opacity 1s ease-out'
          }}>
            <LivePulseBanner />
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

/* ─── Stage Content (stages 2–11) ─── */
const STAGE_CONTENT = {
  2: {
    title: "Signal Received — Multi-channel intake",
    render: () => (
      <div>
        <ul style={{ color: '#475569', lineHeight: 1.8, paddingLeft: '20px', marginBottom: '20px' }}>
          <li>Sourcing requests arrive from ecosystem partners, internal teams, and government channels</li>
          <li>Multi-format intake: PDF uploads, manual forms, API feeds, email forwarding</li>
          <li>AI auto-classifies urgency, sector, and technology domain on arrival</li>
          <li>Each signal creates a trackable case with full provenance chain</li>
        </ul>
        <a href="/proposals" style={{ color: '#0D9488', fontSize: '13px', textDecoration: 'none', fontWeight: 500 }}>
          Try it → Proposals
        </a>
      </div>
    )
  },

  3: {
    title: "Case Structured — AI extracts and classifies",
    render: () => (
      <div>
        <ul style={{ color: '#475569', lineHeight: 1.8, paddingLeft: '20px', marginBottom: '20px' }}>
          <li>AI extracts company info, technology type, sector, and maturity level from uploaded documents</li>
          <li>Sourcing needs classified against Dubai's D33 economic agenda priorities</li>
          <li>Missing fields flagged for analyst review before proceeding</li>
          <li>Structured case record auto-linked to relevant business group</li>
        </ul>
        <a href="/proposals" style={{ color: '#0D9488', fontSize: '13px', textDecoration: 'none', fontWeight: 500 }}>
          Try it → Proposals
        </a>
      </div>
    )
  },

  4: {
    title: "Vendors Discovered — proactive AI matching",
    render: () => (
      <div>
        <ul style={{ color: '#475569', lineHeight: 1.8, paddingLeft: '20px', marginBottom: '20px' }}>
          <li>AI searches the vendor registry to match capabilities to case requirements</li>
          <li>vScore-ranked shortlist generated with match rationale for each vendor</li>
          <li>New vendors auto-onboarded with profile creation on first submission</li>
          <li>Historical performance and compliance status surfaced alongside each match</li>
        </ul>
        <a href="/vendors" style={{ color: '#0D9488', fontSize: '13px', textDecoration: 'none', fontWeight: 500 }}>
          Try it → Vendors
        </a>
      </div>
    )
  },

  5: {
    title: "Compliance Gate — rule-based pre-screening",
    render: () => (
      <div>
        <ul style={{ color: '#475569', lineHeight: 1.8, paddingLeft: '20px', marginBottom: '20px' }}>
          <li>Automated checks against DESC ISR V3, AI Security Policy, and CSP Standards</li>
          <li>Data residency violations flagged before any AI evaluation begins</li>
          <li>Mandatory certifications verified: ISO 27001, ISO 27017, CSA CCM v4</li>
        </ul>
        <a href="/compliance-audits" style={{ color: '#0D9488', fontSize: '13px', textDecoration: 'none', fontWeight: 500 }}>
          Try it → Compliance Audits
        </a>
      </div>
    )
  },

  6: {
    title: "AI Evaluation — 5-dimension scoring with evidence",
    render: () => (
      <div>
        <ul style={{ color: '#475569', lineHeight: 1.8, paddingLeft: '20px', marginBottom: '20px' }}>
          <li>Multi-model AI (Claude, GPT-4o, Gemini) scores across 5 dimensions to eliminate single-model bias</li>
          <li>Full reasoning and evidence attribution provided for every score</li>
          <li>Evidence Validation Layer verifies every claim against source documents</li>
          <li>Claims classified as Grounded, Partial, or Ungrounded by a second AI pass</li>
        </ul>
        <a href="/evaluations" style={{ color: '#0D9488', fontSize: '13px', textDecoration: 'none', fontWeight: 500 }}>
          Try it → Evaluations
        </a>
      </div>
    )
  },

  7: {
    title: "Stage-Gate — human decision authority",
    render: () => (
      <div>
        <ul style={{ color: '#475569', lineHeight: 1.8, paddingLeft: '20px', marginBottom: '20px' }}>
          <li>Committee reviews AI scores, compliance status, and vendor profiles</li>
          <li>GO / KILL / HOLD decisions recorded with rationale and accountability</li>
          <li>Side-by-side proposal comparison with automatic highest-scorer highlighting</li>
        </ul>
        <a href="/compare" style={{ color: '#0D9488', fontSize: '13px', textDecoration: 'none', fontWeight: 500 }}>
          Try it → Compare
        </a>
      </div>
    )
  },

  8: {
    title: "Pilot Tracking — from setup to outcomes",
    render: () => (
      <div>
        <ul style={{ color: '#475569', lineHeight: 1.8, paddingLeft: '20px', marginBottom: '20px' }}>
          <li>Approved vendors enter structured pilot programs with defined success metrics</li>
          <li>Milestone tracking from kickoff through measured business outcomes</li>
          <li>σI Impact Meter calculates analyst-hours saved and total AI cost in real time</li>
          <li>Executive Board Brief generated on demand — professional PDF for leadership</li>
        </ul>
        <a href="/dashboard" style={{ color: '#0D9488', fontSize: '13px', textDecoration: 'none', fontWeight: 500 }}>
          Try it → Dashboard
        </a>
      </div>
    )
  },

  9: {
    title: "Compliance — DESC, OWASP, Ethics, Audit Evidence Pack",
    render: () => (
      <div>
        <ul style={{ color: '#475569', lineHeight: 1.8, paddingLeft: '20px', marginBottom: '20px' }}>
          <li>Platform audits itself: live DESC compliance self-check across 19 controls</li>
          <li>OWASP security controls embedded at the architecture level</li>
          <li>Ethics framework ensures responsible AI with full transparency</li>
          <li>Incident management system tracks, resolves, and reports security events to DESC</li>
        </ul>
        <a href="/compliance-audits" style={{ color: '#0D9488', fontSize: '13px', textDecoration: 'none', fontWeight: 500 }}>
          Try it → Compliance Audits
        </a>
      </div>
    )
  },

  10: {
    title: "Ecosystem Intelligence — Board Brief, KPIs, analytics",
    render: () => (
      <div>
        <ul style={{ color: '#475569', lineHeight: 1.8, paddingLeft: '20px', marginBottom: '20px' }}>
          <li>AI-generated market intelligence reports covering any time period</li>
          <li>Sector breakdowns, technology trends, and D33 alignment scores</li>
          <li>KPI dashboards with live platform metrics updating in real time</li>
          <li>One-click PDF export for board meetings and stakeholder presentations</li>
        </ul>
        <a href="/dashboard" style={{ color: '#0D9488', fontSize: '13px', textDecoration: 'none', fontWeight: 500 }}>
          Try it → Dashboard
        </a>
      </div>
    )
  },

  11: {
    title: "σI Transparency",
    render: () => null // Handled by RevealSection in main render
  },
};

/* ─── Problem Section (Stage 1) ─── */
function ProblemSection() {
  const stats = [
    { value: '1,690+', label: 'startups supported (2025)' },
    { value: '114', label: 'Business in Dubai partners' },
    { value: '35+', label: 'Business Groups' },
    { value: '7,500+', label: 'startups on Ignyte' },
  ];

  return (
    <div style={{ maxWidth: '800px', width: '100%', padding: '40px', textAlign: 'center' }}>
      <h2 style={{ fontSize: '28px', fontWeight: 600, color: '#1E293B', marginBottom: '16px' }}>
        The Problem We Solve
      </h2>
      <p style={{
        color: '#475569', lineHeight: 1.8, fontSize: '15px',
        marginBottom: '32px', maxWidth: '700px', margin: '0 auto 32px'
      }}>
        Dubai Chambers manages 1,690+ startups through Business in Dubai,
        35+ Business Groups surfacing sector needs, Expand North Star
        connecting startups with 1,200+ investors, and 7,500+ startups
        on Ignyte — all flowing through disconnected channels with no
        unified lifecycle visibility.
      </p>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: '16px',
      }}>
        {stats.map((s, i) => (
          <div key={i} style={{
            background: '#F0FDFA', border: '1px solid #99F6E4',
            borderRadius: '12px', padding: '24px 16px', textAlign: 'center',
          }}>
            <div style={{
              fontSize: '28px', fontWeight: 700, color: '#0D9488', marginBottom: '8px'
            }}>
              {s.value}
            </div>
            <div style={{ fontSize: '13px', color: '#475569', lineHeight: 1.4 }}>
              {s.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

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

/* ─── Reveal Section (Stage 10) ─── */
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

/* ─── About Section (Stage 12) ─── */
function AboutSection() {
  return (
    <div style={{ maxWidth: '700px', width: '100%', padding: '40px', textAlign: 'center' }}>
      <h2 style={{ fontSize: '24px', fontWeight: 500, color: '#1E293B', marginBottom: '20px' }}>
        About
      </h2>
      <p style={{ color: '#475569', lineHeight: 1.8, fontSize: '16px' }}>
        Conceived and architected by Tamer Momtaz, Lead R&amp;D at Devoneers.
        Powered by σI (Added Intelligence). Ready for commercial partnership
        — Phase 1 deploys on DESC-certified infrastructure in 12 weeks.
      </p>
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

  const next = () => setCurrentStage(prev => Math.min(prev + 1, 13));
  const back = () => setCurrentStage(prev => Math.max(prev - 1, 0));
  const jumpTo = (stage) => setCurrentStage(stage);
  const startJourney = () => { setCurrentStage(1); };

  // Render hero if stage 0
  if (currentStage === 0) {
    return <HeroSection onStart={startJourney} impact={impactData} session={session} />;
  }

  // Stage 1: The Problem We Solve
  if (currentStage === 1) {
    return (
      <div style={{ minHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
          <ProblemSection />
        </div>
        <NavigationBar current={1} total={12} stageName="The Problem" onNext={next} onBack={back} onJump={jumpTo} isLast={false} />
      </div>
    );
  }

  // Stage 11 gets the dark cinematic treatment (like the hero)
  if (currentStage === 11) {
    return (
      <div style={{ minHeight: 'calc(100vh - 64px)', background: '#0F172A', display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden' }}>
        <ParticleField />
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', zIndex: 2, padding: '2rem' }}>
          <RevealSection impact={impactData} />
        </div>
        <div style={{ position: 'relative', zIndex: 10, borderTop: '0.5px solid rgba(255,255,255,0.1)', background: 'rgba(15,23,42,0.8)' }}>
          <NavigationBar current={11} total={12} stageName="σI Transparency" onNext={next} onBack={back} onJump={jumpTo} isLast={false} />
        </div>
      </div>
    );
  }

  // Stage 12: About
  if (currentStage === 12) {
    return (
      <div style={{ minHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
          <AboutSection />
        </div>
        <NavigationBar current={12} total={12} stageName="About" onNext={next} onBack={back} onJump={jumpTo} isLast={true} />
      </div>
    );
  }

  // Render finale if stage 13
  if (currentStage === 13) {
    return (
      <div style={{ minHeight: 'calc(100vh - 64px)', background: '#0F172A', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' }}>
        <ParticleField />
        <FinaleSection
          impact={impactData}
          onReplay={() => setCurrentStage(0)}
          onExplore={() => navigate('/dashboard')}
          onBack={() => setCurrentStage(12)}
        />
      </div>
    );
  }

  // Stages 2-10: normal content cards
  return (
    <div style={{ minHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
        <StageCard stage={currentStage} />
      </div>
      <NavigationBar current={currentStage} total={12} stageName={STAGES[currentStage]?.name} onNext={next} onBack={back} onJump={jumpTo} isLast={false} />
    </div>
  );
}
