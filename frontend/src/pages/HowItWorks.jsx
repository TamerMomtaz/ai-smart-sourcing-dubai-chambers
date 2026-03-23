import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import api from '../lib/api';

/* ─── Animated counter hook ─── */
function useCountUp(target, duration = 1200, start = true) {
  const [value, setValue] = useState(0);
  const rafRef = useRef(null);
  const startRef = useRef(null);

  useEffect(() => {
    if (!start || target == null || target === 0) { setValue(0); return; }
    const t = Number(target);
    startRef.current = performance.now();
    const animate = (now) => {
      const elapsed = now - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(eased * t);
      if (progress < 1) rafRef.current = requestAnimationFrame(animate);
      else setValue(t);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [target, duration, start]);

  return value;
}

/* ─── Reduced motion detection ─── */
function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(mq.matches);
    const handler = (e) => setReduced(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);
  return reduced;
}

/* ─── Pipeline SVG ─── */
const STAGE_LABELS = ['Submit', 'Evaluate', 'Verify', 'Audit', 'Report'];

function PipelineViz({ currentStage, onNodeClick, reducedMotion }) {
  const nodeSpacing = 140;
  const nodeR = 20;
  const svgWidth = 4 * nodeSpacing + 2 * nodeR + 60;
  const svgHeight = 60;

  return (
    <div className="w-full overflow-x-auto pb-2">
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="mx-auto block"
        style={{ minWidth: 600, maxWidth: 780 }}
        aria-label="Pipeline stages"
      >
        {/* Connecting lines */}
        {[0, 1, 2, 3].map((i) => {
          const x1 = 30 + i * nodeSpacing + nodeR;
          const x2 = 30 + (i + 1) * nodeSpacing - nodeR;
          const active = currentStage > i + 1;
          const animating = currentStage === i + 2 && !reducedMotion;
          return (
            <line
              key={`line-${i}`}
              x1={x1} y1={svgHeight / 2}
              x2={x2} y2={svgHeight / 2}
              stroke={active || animating ? '#0D9488' : '#334155'}
              strokeWidth={2}
              strokeDasharray={animating ? '6 4' : 'none'}
              style={animating ? {
                animation: 'lineDash 0.8s linear forwards',
              } : {
                transition: 'stroke 0.5s ease-out',
              }}
            />
          );
        })}
        {/* Nodes */}
        {STAGE_LABELS.map((label, i) => {
          const cx = 30 + i * nodeSpacing;
          const active = currentStage >= i + 1;
          return (
            <g
              key={label}
              onClick={() => onNodeClick(i + 1)}
              style={{ cursor: 'pointer' }}
              role="button"
              aria-label={`Stage ${i + 1}: ${label}`}
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onNodeClick(i + 1)}
            >
              <circle
                cx={cx} cy={svgHeight / 2} r={nodeR}
                fill={active ? '#0D9488' : '#1E293B'}
                stroke={active ? '#0D9488' : '#334155'}
                strokeWidth={2}
                style={{ transition: reducedMotion ? 'none' : 'fill 0.5s ease-out, stroke 0.5s ease-out' }}
              />
              <text
                x={cx} y={svgHeight / 2 + 1}
                textAnchor="middle" dominantBaseline="central"
                fill="white" fontSize="13" fontWeight="bold"
                style={{ pointerEvents: 'none', fontFamily: 'var(--font-body)' }}
              >
                {i + 1}
              </text>
              <text
                x={cx} y={svgHeight / 2 + nodeR + 14}
                textAnchor="middle"
                fill={active ? '#0D9488' : '#94A3B8'}
                fontSize="11"
                style={{ pointerEvents: 'none', fontFamily: 'var(--font-body)', transition: 'fill 0.3s' }}
              >
                {label}
              </text>
            </g>
          );
        })}
        {/* PDF icon before first node */}
        {currentStage >= 1 && (
          <g style={reducedMotion ? {} : { animation: 'fadeSlideRight 0.5s ease-out' }}>
            <rect x={-6} y={svgHeight / 2 - 10} width={20} height={20} rx={3} fill="#1E293B" stroke="#0D9488" strokeWidth={1.5} />
            <text x={4} y={svgHeight / 2 + 1} textAnchor="middle" dominantBaseline="central" fill="#0D9488" fontSize="7" fontWeight="bold" style={{ fontFamily: 'var(--font-mono)' }}>
              PDF
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}

/* ─── Score Bar ─── */
function ScoreBar({ label, score, delay, active, reducedMotion }) {
  return (
    <div className="flex items-center gap-3 text-sm" style={!reducedMotion && active ? { animation: `typeIn 0.4s ease-out ${delay}s both` } : {}}>
      <span className="text-gray-400 w-24 text-right font-body text-xs">{label}</span>
      <div className="flex-1 h-1.5 bg-[#1E293B] rounded-full overflow-hidden">
        <div
          className="h-full bg-[#0D9488] rounded-full"
          style={{
            width: active ? `${score}%` : '0%',
            transition: reducedMotion ? 'none' : `width 0.8s ease-out ${delay}s`,
          }}
        />
      </div>
      <span className="text-[#0D9488] font-mono text-xs w-8">{active ? score : 0}</span>
    </div>
  );
}

/* ─── Stage Card ─── */
function StageCard({ stage, active, reducedMotion }) {
  if (!active) return null;

  const animClass = reducedMotion ? '' : 'animate-slideUp';

  return (
    <div className={`bg-[#1E293B]/80 backdrop-blur-sm rounded-xl border border-[#334155] p-6 sm:p-8 ${animClass}`}>
      {stage}
    </div>
  );
}

/* ─── Claim item ─── */
function ClaimItem({ icon, text, status, color, delay, active, reducedMotion }) {
  const colors = { green: 'text-green-400', amber: 'text-amber-400', red: 'text-red-400' };
  return (
    <div
      className="flex items-start gap-2 text-sm"
      style={!reducedMotion && active ? { animation: `typeIn 0.4s ease-out ${delay}s both` } : {}}
    >
      <span className={colors[color]}>{icon}</span>
      <span className="text-gray-300 font-body">{text}</span>
      <span className={`ml-auto text-xs font-mono ${colors[color]}`}>{status}</span>
    </div>
  );
}

/* ─── Main Component ─── */
function HowItWorks() {
  const [currentStage, setCurrentStage] = useState(0); // 0=hero, 1-5=stages, 6=reveal
  const [impact, setImpact] = useState(null);
  const [loading, setLoading] = useState(true);
  const reducedMotion = usePrefersReducedMotion();
  const pipelineRef = useRef(null);

  // Try to get auth context - will be null for public visitors
  let user = null;
  try {
    const auth = useAuth();
    user = auth?.user ?? null;
  } catch {
    // Outside AuthProvider (shouldn't happen, but safe fallback)
  }

  // Fetch impact data
  useEffect(() => {
    api.get('/api/v1/dashboard/impact')
      .then((res) => setImpact(res.data))
      .catch(() => setImpact(null))
      .finally(() => setLoading(false));
  }, []);

  // Auto-advance stages
  useEffect(() => {
    if (reducedMotion) {
      if (currentStage >= 1 && currentStage <= 5) setCurrentStage(6);
      return;
    }
    if (currentStage >= 1 && currentStage <= 5) {
      const timer = setTimeout(() => setCurrentStage((prev) => prev + 1), 3000);
      return () => clearTimeout(timer);
    }
  }, [currentStage, reducedMotion]);

  const startJourney = useCallback(() => {
    setCurrentStage(1);
    setTimeout(() => {
      pipelineRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }, []);

  const jumpToStage = useCallback((stage) => {
    setCurrentStage(stage);
  }, []);

  const replay = useCallback(() => {
    setCurrentStage(0);
  }, []);

  // Impact numbers
  const proposals = impact?.total_operations ?? 15;
  const hoursSaved = impact?.total_hours_saved ?? 355;
  const totalCost = impact?.total_cost ?? 2.15;
  const totalMinutes = impact?.total_processing_minutes ?? 39;

  // Animated reveal counters
  const revealActive = currentStage === 6;
  const animMinutes = useCountUp(totalMinutes, 1500, revealActive);
  const animHours = useCountUp(hoursSaved, 1500, revealActive);
  const animCost = useCountUp(totalCost, 1500, revealActive);

  /* ─── STAGE CONTENT ─── */

  const stageContent = {
    1: (
      <div className="space-y-4">
        <p className="text-gray-400 font-body text-sm uppercase tracking-wider">Stage 1</p>
        <p className="text-white font-heading text-xl sm:text-2xl">A vendor submits a proposal PDF</p>
        <div className="space-y-2 mt-4">
          <p className="text-[#0D9488] font-mono text-sm" style={reducedMotion ? {} : { animation: 'typeIn 0.5s ease-out 0.3s both' }}>
            CyberShield — Zero-Trust Endpoint Protection Suite
          </p>
          <p className="text-gray-400 font-body text-sm" style={reducedMotion ? {} : { animation: 'typeIn 0.5s ease-out 0.8s both' }}>
            AI extracted: <span className="text-[#0D9488]">Cybersecurity</span> | <span className="text-[#0D9488]">Production</span> | <span className="text-[#0D9488]">Dubai</span> | <span className="text-[#0D9488]">DESC Certified</span>
          </p>
        </div>
      </div>
    ),
    2: (
      <div className="space-y-4">
        <p className="text-gray-400 font-body text-sm uppercase tracking-wider">Stage 2</p>
        <p className="text-white font-heading text-xl sm:text-2xl">Multi-model AI evaluates across 4 dimensions</p>
        <div className="space-y-3 mt-4">
          <ScoreBar label="Relevance" score={92} delay={0.2} active={currentStage >= 2} reducedMotion={reducedMotion} />
          <ScoreBar label="Feasibility" score={88} delay={0.5} active={currentStage >= 2} reducedMotion={reducedMotion} />
          <ScoreBar label="Sector" score={95} delay={0.8} active={currentStage >= 2} reducedMotion={reducedMotion} />
          <ScoreBar label="Compliance" score={94} delay={1.1} active={currentStage >= 2} reducedMotion={reducedMotion} />
        </div>
        <p className="text-gray-400 font-body text-sm mt-4" style={reducedMotion ? {} : { animation: 'typeIn 0.5s ease-out 1.5s both' }}>
          Composite: <span className="text-[#0D9488] font-mono font-medium">92.3</span> — evaluated in <span className="text-[#0D9488] font-mono">23 seconds</span>
        </p>
      </div>
    ),
    3: (
      <div className="space-y-4">
        <p className="text-gray-400 font-body text-sm uppercase tracking-wider">Stage 3</p>
        <p className="text-white font-heading text-xl sm:text-2xl">Hallucination Shield verifies every AI claim</p>
        <div className="space-y-2 mt-4">
          <ClaimItem icon="✓" text={'"ISO 27001 certified"'} status="Grounded" color="green" delay={0.2} active={currentStage >= 3} reducedMotion={reducedMotion} />
          <ClaimItem icon="✓" text={'"12,000 endpoints protected"'} status="Grounded" color="green" delay={0.5} active={currentStage >= 3} reducedMotion={reducedMotion} />
          <ClaimItem icon="~" text={'"50+ professionals"'} status="Partial" color="amber" delay={0.8} active={currentStage >= 3} reducedMotion={reducedMotion} />
          <ClaimItem icon="✗" text={'"Dubai Police deployment"'} status="Ungrounded" color="red" delay={1.1} active={currentStage >= 3} reducedMotion={reducedMotion} />
        </div>
        <p className="text-gray-400 font-body text-sm mt-4" style={reducedMotion ? {} : { animation: 'typeIn 0.5s ease-out 1.5s both' }}>
          Grounding score: <span className="text-[#0D9488] font-mono font-medium">61.4%</span> — 2 claims flagged for review
        </p>
      </div>
    ),
    4: (
      <div className="space-y-4">
        <p className="text-gray-400 font-body text-sm uppercase tracking-wider">Stage 4</p>
        <p className="text-white font-heading text-xl sm:text-2xl">DESC compliance audit runs automatically</p>
        <div className="flex flex-wrap gap-3 mt-4">
          {[
            { label: 'ISR V3', status: 'Pass', icon: '✓', color: 'border-green-500 text-green-400' },
            { label: 'AI Security', status: 'Pass', icon: '✓', color: 'border-green-500 text-green-400' },
            { label: 'CSP', status: 'Warning', icon: '⚠', color: 'border-amber-500 text-amber-400' },
          ].map((badge, i) => (
            <span
              key={badge.label}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm font-mono ${badge.color} bg-[#0F172A]/50`}
              style={reducedMotion ? {} : { animation: `typeIn 0.4s ease-out ${0.3 + i * 0.4}s both` }}
            >
              {badge.label}: {badge.status} {badge.icon}
            </span>
          ))}
        </div>
        <p className="text-amber-400 font-body text-sm mt-4" style={reducedMotion ? {} : { animation: 'typeIn 0.5s ease-out 1.5s both' }}>
          Data residency: <span className="font-mono">Flagged</span> — vendor data outside UAE
        </p>
      </div>
    ),
    5: (
      <div className="space-y-4">
        <p className="text-gray-400 font-body text-sm uppercase tracking-wider">Stage 5</p>
        <p className="text-white font-heading text-xl sm:text-2xl">Intelligence report generated</p>
        <div
          className="mt-4 bg-[#0F172A] rounded-lg border border-[#334155] p-5"
          style={reducedMotion ? {} : { animation: 'typeIn 0.6s ease-out 0.3s both' }}
        >
          <p className="text-white font-heading text-base">Q1 2026 Smart Sourcing Report</p>
          <p className="text-gray-400 font-body text-sm mt-1">15 proposals | 11 sectors | D33 aligned</p>
        </div>
        <p className="text-gray-400 font-body text-sm mt-4" style={reducedMotion ? {} : { animation: 'typeIn 0.5s ease-out 1s both' }}>
          Executive Board Brief ready for download
        </p>
      </div>
    ),
  };

  return (
    <div className="bg-[#0F172A] min-h-screen text-white hiw-container">
      <style>{`
        @keyframes slideUp {
          from { transform: translateY(40px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        @keyframes typeIn {
          from { opacity: 0; transform: translateX(-8px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes fadeSlideRight {
          from { opacity: 0; transform: translateX(-20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes lineDash {
          from { stroke-dashoffset: 40; }
          to { stroke-dashoffset: 0; }
        }
        @keyframes pulseGlow {
          0%, 100% { opacity: 0.7; }
          50% { opacity: 1; }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes countReveal {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-slideUp {
          animation: slideUp 0.5s ease-out;
        }
        @media (prefers-reduced-motion: reduce) {
          .animate-slideUp,
          [style*="animation"] {
            animation: none !important;
            opacity: 1 !important;
            transform: none !important;
          }
        }
      `}</style>

      {/* ─── HERO SECTION ─── */}
      {currentStage === 0 && (
        <section className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
          {/* σI Symbol */}
          <div
            className="text-[#0D9488] text-7xl sm:text-8xl font-heading font-bold mb-6 select-none"
            style={reducedMotion ? {} : { animation: 'pulseGlow 3s ease-in-out infinite' }}
          >
            &sigma;I
          </div>

          {/* Title */}
          <h1 className="font-heading text-3xl sm:text-4xl text-white mb-3">
            AI Smart Sourcing
          </h1>
          <p className="text-gray-400 font-body text-base sm:text-lg mb-10">
            Watch the platform work.
          </p>

          {/* Start button */}
          <button
            onClick={startJourney}
            className="px-8 py-3 bg-[#0D9488] text-white font-body font-medium rounded-lg hover:bg-[#0D9488]/90 transition-colors text-base"
          >
            Start the journey &rarr;
          </button>

          {/* Live stats */}
          <p className="text-gray-500 font-mono text-xs mt-8">
            {loading ? (
              <span className="inline-block w-48 h-4 bg-[#1E293B] rounded animate-pulse" />
            ) : (
              <>
                {proposals} proposals processed &middot; {Math.round(hoursSaved)} hours saved &middot; ${totalCost.toFixed(2)} total cost
              </>
            )}
          </p>

          {/* Auth-dependent link */}
          {!user && (
            <Link to="/login" className="text-[#0D9488] font-body text-sm mt-4 hover:underline">
              Sign in to explore the full platform
            </Link>
          )}
        </section>
      )}

      {/* ─── PIPELINE SECTION ─── */}
      {currentStage >= 1 && (
        <section ref={pipelineRef} className="min-h-screen px-4 sm:px-6 pt-12 pb-20 max-w-3xl mx-auto">
          {/* Pipeline visualization */}
          <div className="mb-10">
            <PipelineViz
              currentStage={currentStage}
              onNodeClick={jumpToStage}
              reducedMotion={reducedMotion}
            />
          </div>

          {/* Stage cards */}
          {currentStage >= 1 && currentStage <= 5 && (
            <StageCard
              key={currentStage}
              stage={stageContent[currentStage]}
              active={true}
              reducedMotion={reducedMotion}
            />
          )}

          {/* ─── REVEAL SECTION ─── */}
          {currentStage === 6 && (
            <div className="text-center space-y-6 mt-8">
              <div style={reducedMotion ? {} : { animation: 'countReveal 0.8s ease-out 0.2s both' }}>
                <p className="text-white font-heading text-xl sm:text-2xl">
                  All of this took <span className="text-[#0D9488] font-mono font-bold">{Math.round(animMinutes)} minutes</span> of AI time.
                </p>
              </div>
              <div style={reducedMotion ? {} : { animation: 'countReveal 0.8s ease-out 1.2s both' }}>
                <p className="text-white font-heading text-xl sm:text-2xl">
                  Replacing <span className="text-[#0D9488] font-mono font-bold">{Math.round(animHours)} hours</span> of manual analysis.
                </p>
              </div>
              <div style={reducedMotion ? {} : { animation: 'countReveal 0.8s ease-out 2.2s both' }}>
                <p className="text-white font-heading text-xl sm:text-2xl">
                  At a total cost of <span className="text-[#0D9488] font-mono font-bold">${animCost.toFixed(2)}</span>.
                </p>
              </div>
              <div style={reducedMotion ? {} : { animation: 'countReveal 0.8s ease-out 3.2s both' }}>
                <p className="text-[#0D9488] font-heading text-lg sm:text-xl mt-4">
                  Added Intelligence — Awareness Implemented
                </p>
              </div>

              {/* CTA */}
              <div className="pt-10" style={reducedMotion ? {} : { animation: 'fadeIn 0.8s ease-out 4s both' }}>
                {user ? (
                  <div>
                    <p className="text-gray-400 font-body text-sm mb-6">Explore the platform</p>
                    <div className="flex flex-wrap justify-center gap-4">
                      <Link to="/dashboard" className="px-6 py-2.5 bg-[#1E293B] text-white font-body text-sm rounded-lg border border-[#334155] hover:border-[#0D9488] transition-colors">
                        Dashboard
                      </Link>
                      <Link to="/proposals" className="px-6 py-2.5 bg-[#1E293B] text-white font-body text-sm rounded-lg border border-[#334155] hover:border-[#0D9488] transition-colors">
                        Proposals
                      </Link>
                      <Link to="/compare" className="px-6 py-2.5 bg-[#1E293B] text-white font-body text-sm rounded-lg border border-[#334155] hover:border-[#0D9488] transition-colors">
                        Compare
                      </Link>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <Link to="/login" className="inline-block px-8 py-3 bg-[#0D9488] text-white font-body font-medium rounded-lg hover:bg-[#0D9488]/90 transition-colors">
                      Sign in to explore
                    </Link>
                  </div>
                )}
              </div>

              {/* Replay */}
              <button
                onClick={replay}
                className="text-gray-500 font-body text-sm mt-6 hover:text-[#0D9488] transition-colors"
              >
                ↻ Replay
              </button>
            </div>
          )}
        </section>
      )}

      {/* Attribution */}
      <footer className="text-center pb-6 px-4">
        <p className="text-gray-600 font-body text-xs">AI Smart Sourcing — Dubai Chambers</p>
        <p className="text-gray-700 font-body text-xs mt-1">Created by Tamer Momtaz | Powered by &sigma;I</p>
      </footer>
    </div>
  );
}

export default HowItWorks;
