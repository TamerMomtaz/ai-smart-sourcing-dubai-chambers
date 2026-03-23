import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';

// Animated counter hook (same pattern as Dashboard)
function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0);
  const rafRef = useRef(null);
  const startRef = useRef(null);

  useEffect(() => {
    if (target == null || target === 0) { setValue(0); return; }
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
  }, [target, duration]);

  return value;
}

// Skeleton pulse for loading state
const Skeleton = () => (
  <span className="inline-block w-16 h-5 bg-[#0D9488]/20 rounded animate-pulse align-middle" />
);

// Metric display with animated count
const LiveMetric = ({ icon, value, suffix, loading, decimals = 0 }) => {
  const animated = useCountUp(loading ? 0 : value);
  return (
    <span className="inline-flex items-center gap-1.5 text-sm font-mono text-[#0D9488]">
      {icon}
      {loading ? <Skeleton /> : (
        <span>{decimals > 0 ? animated.toFixed(decimals) : Math.round(animated)}{suffix}</span>
      )}
    </span>
  );
};

// SVG icons for each step (simple, clean)
const StepIcons = {
  submit: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  evaluate: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  verify: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  audit: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
    </svg>
  ),
  report: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
    </svg>
  ),
};

function HowItWorks() {
  const [stats, setStats] = useState(null);
  const [impact, setImpact] = useState(null);
  const [shieldStats, setShieldStats] = useState(null);
  const [aiSummary, setAiSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, impactRes, shieldRes, aiRes] = await Promise.all([
          api.get('/api/v1/dashboard/stats').catch(() => ({ data: null })),
          api.get('/api/v1/dashboard/impact').catch(() => ({ data: null })),
          api.get('/api/v1/hallucination/stats').catch(() => ({ data: null })),
          api.get('/api/v1/ai-interactions/summary').catch(() => ({ data: null })),
        ]);
        setStats(statsRes.data);
        setImpact(impactRes.data);
        setShieldStats(shieldRes.data);
        setAiSummary(aiRes.data);
      } catch (e) {
        // Silently handle — metrics just won't show
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const proposalCount = stats?.proposals?.total ?? 0;
  const evaluationCount = stats?.evaluations?.total ?? 0;
  const avgScore = stats?.evaluations?.average_score ?? 0;
  const auditCount = stats?.compliance_audits?.total ?? 0;
  const trendCount = stats?.trend_analyses?.total ?? 0;
  const shieldCount = shieldStats?.total_checks ?? 0;
  const avgGrounding = shieldStats?.average_grounding_score ?? 0;
  const hoursSaved = impact?.total_hours_saved ?? 0;
  const totalCost = impact?.total_cost ?? 0;
  const totalMinutes = impact?.total_processing_minutes ?? 0;

  const steps = [
    {
      num: 1,
      title: 'Submit a Proposal',
      icon: StepIcons.submit,
      description: 'Vendors drop a PDF or fill in details.',
      bullets: [
        'AI extracts company info, technology, sector, and maturity level automatically',
        'Supports PDF upload or manual form entry',
        'Vendor record auto-created if needed',
      ],
      link: { label: 'Go to Proposals', to: '/proposals' },
      metric: <LiveMetric icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-3-3v6m-7 4h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>} value={proposalCount} suffix=" proposals received" loading={loading} />,
    },
    {
      num: 2,
      title: 'AI Evaluation',
      icon: StepIcons.evaluate,
      description: 'Multi-model AI scores each proposal on 4 dimensions.',
      bullets: [
        'Relevance, Feasibility, Sector Alignment, and DESC Compliance',
        'Takes ~25 seconds per proposal',
        'Cross-model consensus scoring for accuracy',
      ],
      link: { label: 'Go to Evaluations', to: '/evaluations' },
      metric: <><LiveMetric icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>} value={evaluationCount} suffix=" evaluations completed" loading={loading} />{!loading && avgScore > 0 && <span className="text-sm font-mono text-[#0D9488] ml-2">| Avg: {avgScore.toFixed(1)}</span>}</>,
    },
    {
      num: 3,
      title: 'Hallucination Shield',
      icon: StepIcons.verify,
      description: 'A second AI pass verifies every claim the evaluation made.',
      bullets: [
        'Each claim is traced back to the source document',
        'Cross-model scoring detects anomalies',
        'DESC Monitor phase ensures governance compliance',
      ],
      link: { label: 'Go to Evaluations \u2192 View \u2192 Shield', to: '/evaluations' },
      metric: <><LiveMetric icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>} value={shieldCount} suffix=" checks run" loading={loading} />{!loading && avgGrounding > 0 && <span className="text-sm font-mono text-[#0D9488] ml-2">| Avg grounding: {avgGrounding.toFixed(1)}%</span>}</>,
    },
    {
      num: 4,
      title: 'DESC Compliance Audit',
      icon: StepIcons.audit,
      description: 'Automated review against 3 governance frameworks.',
      bullets: [
        'DESC ISR V3, AI Security Policy (5-phase lifecycle), and CSP Standards',
        'Flags specific controls that pass or fail with evidence',
        'Full audit trail for accountability',
      ],
      link: { label: 'Go to Compliance Audits', to: '/compliance-audits' },
      metric: <LiveMetric icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>} value={auditCount} suffix=" audits completed" loading={loading} />,
    },
    {
      num: 5,
      title: 'Intelligence & Reporting',
      icon: StepIcons.report,
      description: 'AI-generated trend reports with sector breakdown and D33 alignment.',
      bullets: [
        'Quarterly trend analysis with recommendations',
        'One-click Executive Board Brief for leadership',
        'Sector-level insights for strategic decision-making',
      ],
      links: [
        { label: 'Trend Analyses', to: '/trend-analyses' },
        { label: 'Board Brief', to: '/board-brief' },
      ],
      metric: <LiveMetric icon={<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M7 12l3-3 3 3 4-4" /></svg>} value={trendCount} suffix=" reports generated" loading={loading} />,
    },
  ];

  return (
    <div className="max-w-3xl mx-auto py-4">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="font-heading text-3xl sm:text-4xl text-teal mb-3">
          How AI Smart Sourcing Works
        </h1>
        <p className="font-body text-ink/70 text-base sm:text-lg">
          From proposal to decision &mdash; powered by &sigma;I
        </p>
      </div>

      {/* Steps */}
      <div className="relative">
        {steps.map((step, idx) => (
          <div key={step.num} className="relative">
            {/* Connecting line */}
            {idx < steps.length - 1 && (
              <div className="absolute left-6 top-full w-0.5 h-8 bg-[#0D9488]/30 z-0" />
            )}

            {/* Step card */}
            <div className="relative bg-white rounded-xl shadow-sm border-l-4 border-[#0D9488] p-6 mb-8 hover:shadow-md transition-shadow">
              {/* Step number + title row */}
              <div className="flex items-start gap-4 mb-3">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-heading text-lg font-bold">
                  {step.num}
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="font-heading text-lg sm:text-xl text-ink leading-tight">
                    {step.title}
                  </h2>
                  <p className="font-body text-ink/70 text-sm mt-1">
                    {step.description}
                  </p>
                </div>
                <div className="flex-shrink-0 text-[#0D9488] hidden sm:block">
                  {step.icon}
                </div>
              </div>

              {/* What happens */}
              <div className="ml-14 mb-4">
                <p className="font-body text-xs text-ink/50 uppercase tracking-wider mb-2">What happens</p>
                <ul className="space-y-1.5">
                  {step.bullets.map((b, i) => (
                    <li key={i} className="font-body text-sm text-ink/80 flex items-start gap-2">
                      <span className="text-[#0D9488] mt-0.5 flex-shrink-0">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      </span>
                      {b}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Try it + metric row */}
              <div className="ml-14 flex flex-col sm:flex-row sm:items-center gap-3">
                <div className="flex gap-2">
                  {step.link && (
                    <Link
                      to={step.link.to}
                      className="inline-flex items-center gap-1 text-sm font-body font-medium text-[#0D9488] hover:text-[#0D9488]/80 transition-colors"
                    >
                      <span>&rarr;</span> {step.link.label}
                    </Link>
                  )}
                  {step.links && step.links.map((l, i) => (
                    <React.Fragment key={l.to}>
                      {i > 0 && <span className="text-ink/30">|</span>}
                      <Link
                        to={l.to}
                        className="inline-flex items-center gap-1 text-sm font-body font-medium text-[#0D9488] hover:text-[#0D9488]/80 transition-colors"
                      >
                        <span>&rarr;</span> {l.label}
                      </Link>
                    </React.Fragment>
                  ))}
                </div>
                <div className="sm:ml-auto">
                  {step.metric}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer: Return on Time */}
      <div className="bg-white rounded-xl shadow-sm border border-[#0D9488]/20 p-6 mt-4 mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-full bg-[#0D9488]/10 text-[#0D9488] flex items-center justify-center">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="font-heading text-lg text-ink">Return on Time</h3>
        </div>
        <p className="font-body text-sm text-ink/70 mb-4">
          All of the above &mdash; evaluating, verifying, auditing, and reporting &mdash; was done by AI
          in{' '}
          <span className="font-mono text-[#0D9488] font-medium">
            {loading ? <Skeleton /> : <>{Math.round(totalMinutes)} minutes</>}
          </span>
          {' '}total, saving an estimated{' '}
          <span className="font-mono text-[#0D9488] font-medium">
            {loading ? <Skeleton /> : <>{Math.round(hoursSaved)} analyst-hours</>}
          </span>
          . Total cost:{' '}
          <span className="font-mono text-[#0D9488] font-medium">
            {loading ? <Skeleton /> : <>${totalCost.toFixed(2)}</>}
          </span>
          .
        </p>
        <p className="font-body text-sm text-ink/60 mb-4">
          Every AI interaction is tracked on the &sigma;I Transparency Dashboard &mdash; cost, energy,
          CO&#x2082;, and Intelligence Units.
        </p>
        <Link
          to="/ai-interactions"
          className="inline-flex items-center gap-1 text-sm font-body font-medium text-[#0D9488] hover:text-[#0D9488]/80 transition-colors"
        >
          <span>&rarr;</span> See &sigma;I Transparency
        </Link>
      </div>

      {/* Attribution */}
      <div className="text-center pb-4">
        <p className="font-body text-sm text-ink/60">AI Smart Sourcing &mdash; Dubai Chambers</p>
        <p className="font-body text-xs text-ink/40 mt-1">Created by Tamer Momtaz | Powered by &sigma;I</p>
      </div>
    </div>
  );
}

export default HowItWorks;
