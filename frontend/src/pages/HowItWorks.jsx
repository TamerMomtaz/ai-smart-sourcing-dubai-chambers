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
  { id: 12, name: '\u03C3I Transparency', sidebar: '\u03A3I Transparency' },
  { id: 13, name: 'Finale', sidebar: null },
];

const TOOLTIPS = {
  1: 'Proposals \u2014 submit via PDF upload or manual form',
  2: 'Evaluations \u2014 AI-powered scoring with full reasoning',
  3: 'Evaluations \u2014 Shield verification inside each evaluation',
  4: 'Compliance Audits \u2014 automated DESC framework assessment',
  5: 'Trend Analyses \u2014 on-demand market intelligence with PDF export',
  6: 'Compare \u2014 side-by-side decision-making tool',
  7: 'Dashboard \u2014 live metrics with Impact Meter and Board Brief',
  8: 'Vendors \u2014 profiles with DESC certification status',
  9: 'Documents \u2014 source of truth powering AI accuracy',
  10: 'Business Groups \u2014 sector-specific evaluation configuration',
  11: 'Users \u2014 role-based access management',
  12: '\u03A3I Transparency \u2014 full AI cost and environmental accountability',
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
      minHeight: '100vh', background: '#0F172A', display: 'flex',
      flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden'
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

        {/* "powered by \u03C3I" */}
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
          }}>\u03C3I</span>
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
            <span><span style={{ color: '#0D9488', fontFamily: 'monospace' }}>{impact.summary?.total_proposals || '\u2014'}</span> proposals processed</span>
            <span><span style={{ color: '#0D9488', fontFamily: 'monospace' }}>{impact.time_saved?.total_hours || '\u2014'}</span> analyst-hours saved</span>
            <span><span style={{ color: '#0D9488', fontFamily: 'monospace' }}>${impact.ai_performance?.total_cost_usd || '\u2014'}</span> total AI cost</span>
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
              Explore the platform \u2192
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

/* ─── Stage Card (placeholder for Part 2) ─── */
function StageCard({ stage }) {
  const stageData = STAGES[stage];
  return (
    <div style={{
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
      <h2 style={{ fontSize: '24px', fontWeight: 500, marginBottom: '8px', color: '#fff' }}>
        {stageData?.name}
      </h2>
      <p style={{ color: '#94A3B8' }}>Content coming in Part 2...</p>
    </div>
  );
}

/* ─── Navigation Bar ─── */
function NavigationBar({ current, total, stageName, onNext, onBack, onJump, isLast }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '16px 24px', borderTop: '0.5px solid rgba(255,255,255,0.1)',
      background: 'rgba(15,23,42,0.5)', backdropFilter: 'none'
    }}>
      <button onClick={onBack} disabled={current <= 1}
        style={{
          background: 'none', border: 'none', color: current <= 1 ? '#334155' : '#94A3B8',
          cursor: current <= 1 ? 'default' : 'pointer', fontSize: '14px', padding: '8px 16px'
        }}>
        \u2190 Back
      </button>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {Array.from({ length: total }, (_, i) => (
          <div key={i + 1} onClick={() => onJump(i + 1)}
            style={{
              width: current === i + 1 ? '24px' : '8px',
              height: '8px',
              borderRadius: '4px',
              background: i + 1 <= current ? '#0D9488' : '#334155',
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
          />
        ))}
        <span style={{ color: '#64748B', fontSize: '12px', marginLeft: '12px' }}>
          {current}/12 \u2014 {stageName}
        </span>
      </div>

      <button onClick={onNext}
        style={{
          background: 'none', border: '1px solid #0D9488', color: '#0D9488',
          cursor: 'pointer', fontSize: '14px', padding: '8px 20px', borderRadius: '6px'
        }}>
        {isLast ? 'See the reveal \u2192' : 'Next \u2192'}
      </button>
    </div>
  );
}

/* ─── Finale Section (placeholder for Part 3) ─── */
function FinaleSection({ impact, onReplay, onExplore }) {
  return (
    <div style={{
      minHeight: '100vh', background: '#0F172A',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: '24px'
    }}>
      <p style={{ color: '#94A3B8' }}>Finale coming in Part 3...</p>
      <button onClick={onReplay} style={{
        background: 'none', border: '1px solid #334155', color: '#94A3B8',
        padding: '8px 20px', borderRadius: '6px', cursor: 'pointer', fontSize: '14px'
      }}>
        Replay
      </button>
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

  // Render finale if stage 13
  if (currentStage === 13) {
    return (
      <FinaleSection
        impact={impactData}
        onReplay={() => setCurrentStage(0)}
        onExplore={() => navigate('/dashboard')}
      />
    );
  }

  // Stages 1-12
  return (
    <div style={{ minHeight: '80vh', display: 'flex', flexDirection: 'column', background: '#0F172A' }}>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
        <StageCard stage={currentStage} />
      </div>

      <NavigationBar
        current={currentStage}
        total={12}
        stageName={STAGES[currentStage]?.name}
        onNext={next}
        onBack={back}
        onJump={jumpTo}
        isLast={currentStage === 12}
      />
    </div>
  );
}
