import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from '../lib/language';
import api from '../lib/api';

/* ------------------------------------------------------------------ */
/*  Animated counter hook                                              */
/* ------------------------------------------------------------------ */
function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    if (target == null || target === 0) { setValue(0); return; }
    let start = 0;
    const step = Math.ceil(target / (duration / 16));
    const id = setInterval(() => {
      start += step;
      if (start >= target) { setValue(target); clearInterval(id); }
      else setValue(start);
    }, 16);
    ref.current = id;
    return () => clearInterval(ref.current);
  }, [target, duration]);

  return value;
}

/* ------------------------------------------------------------------ */
/*  Single stat with count-up                                          */
/* ------------------------------------------------------------------ */
function LiveStat({ label, value, suffix }) {
  const display = useCountUp(value);
  return (
    <div className="flex items-center gap-2 mt-3 text-sm font-semibold text-ink/80">
      <span className="inline-block w-2 h-2 rounded-full bg-teal animate-pulse" />
      <span>{display.toLocaleString()}{suffix || ''}</span>
      <span className="text-ink/50 font-normal">{label}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Agent card                                                         */
/* ------------------------------------------------------------------ */
function AgentCard({ agent, stats }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      className="relative bg-white rounded-xl shadow-md overflow-hidden transition-all duration-300"
      style={{
        borderLeft: `5px solid ${agent.color}`,
        boxShadow: hovered
          ? `0 8px 30px ${agent.color}30, 0 2px 8px rgba(0,0,0,0.08)`
          : '0 1px 3px rgba(0,0,0,0.1)',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-3">
          <span className="text-3xl">{agent.icon}</span>
          <div>
            <h3 className="font-heading text-lg font-bold" style={{ color: agent.color }}>
              {agent.name}
            </h3>
            <p className="text-xs text-ink/50 font-medium">{agent.subtitle}</p>
          </div>
        </div>

        {/* Role description */}
        <p className="text-sm text-ink/70 leading-relaxed mb-4">{agent.role}</p>

        {/* Powers badges */}
        <div className="flex flex-wrap gap-1.5 mb-2">
          {agent.powers.map((p) => (
            <span
              key={p}
              className="px-2 py-0.5 rounded-full text-[11px] font-medium"
              style={{
                background: `${agent.color}15`,
                color: agent.color,
                border: `1px solid ${agent.color}30`,
              }}
            >
              {p}
            </span>
          ))}
        </div>

        {/* Live stat */}
        {agent.statRender(stats)}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Agent definitions                                                  */
/* ------------------------------------------------------------------ */
const AGENTS = [
  {
    name: 'SCOUT',
    subtitle: 'Innovation Intake Specialist',
    color: '#F59E0B',
    icon: '\uD83D\uDD0D',
    role: "I receive signals from across Dubai's ecosystem \u2014 Business in Dubai, Ignyte, Business Groups, partner referrals. I structure raw requests into actionable sourcing cases and detect duplicates before they waste resources.",
    powers: ['AI Assist structuring', 'Deduplication', 'Channel intake'],
    statRender: (s) => <LiveStat label="sourcing cases processed" value={s?.scout?.sourcing_cases_count} />,
  },
  {
    name: 'MATCH',
    subtitle: 'Vendor Discovery Specialist',
    color: '#8B5CF6',
    icon: '\uD83C\uDFAF',
    role: 'I search the vendor pool to find the best matches for every sourcing case. I analyze capabilities, compliance status, past performance, and trust scores to rank candidates.',
    powers: ['Active vendor matching', 'vScore analysis', 'Factsheet generation'],
    statRender: (s) => <LiveStat label="vendors in pool" value={s?.match?.vendors_count} />,
  },
  {
    name: 'SENTINEL',
    subtitle: 'Compliance Gate Officer',
    color: '#EF4444',
    icon: '\uD83D\uDEE1\uFE0F',
    role: 'Before any AI tokens are spent, I run 5 deterministic checks: DESC certification, data residency, certifications, duplicates, and completeness. I\u2019m the first line of defense.',
    powers: ['Compliance Gate', 'Document sanitization', 'Prompt injection detection'],
    statRender: (s) => <LiveStat label="gate checks run" value={s?.sentinel?.gate_checks_count} />,
  },
  {
    name: 'EVALUATOR',
    subtitle: 'Multi-Dimensional Scorer',
    color: '#10B981',
    icon: '\uD83E\uDDE0',
    role: 'I score proposals across 5 dimensions \u2014 Relevance, Feasibility, Compliance, Sector Alignment, and Innovation Novelty. Every score comes with evidence attribution. Every claim is traceable.',
    powers: ['5-dimension scoring', 'Evidence attribution', 'Contextual evaluation'],
    statRender: (s) => (
      <>
        <LiveStat label="evaluations completed" value={s?.evaluator?.evaluations_count} />
        {s?.evaluator?.avg_composite_score > 0 && (
          <LiveStat label="avg score" value={s?.evaluator?.avg_composite_score} suffix="/100" />
        )}
      </>
    ),
  },
  {
    name: 'VERIFIER',
    subtitle: 'Evidence Validation Specialist',
    color: '#06B6D4',
    icon: '\u2713',
    role: 'I verify every AI conclusion against source evidence. Cross-model verification catches inconsistencies. RAG grounding checks claims against official records. Nothing passes without proof.',
    powers: ['Evidence Validation Layer', 'RAG compliance verification', 'G/P/U classification'],
    statRender: (s) => <LiveStat label="shield checks performed" value={s?.verifier?.shield_checks_count} />,
  },
  {
    name: 'GUARDIAN',
    subtitle: 'Governance & Audit Watcher',
    color: '#F97316',
    icon: '\uD83D\uDCCB',
    role: 'I maintain the immutable audit trail \u2014 every AI operation, every human override, every gate decision. I generate DESC audit evidence packs and verify hash chain integrity. Nothing is modified after the fact.',
    powers: ['Immutable logs', 'Hash chain', 'Audit evidence pack', 'Retention policy', 'Alerts'],
    statRender: (s) => (
      <>
        <LiveStat label="AI operations logged" value={s?.guardian?.ai_interactions_count} />
        {s?.guardian?.integrity_verified && (
          <div className="flex items-center gap-1.5 mt-1 text-xs text-emerald-600 font-medium">
            <span>&#9679;</span> Hash chain integrity verified
          </div>
        )}
      </>
    ),
  },
  {
    name: 'STRATEGIST',
    subtitle: 'Ecosystem Intelligence Analyst',
    color: '#3B82F6',
    icon: '\uD83D\uDCCA',
    role: 'I transform platform data into institutional intelligence. Board Briefs, sector demand analysis, pipeline KPIs, channel analytics, innovation trends \u2014 I help leadership see the full picture.',
    powers: ['Board Brief', 'Ecosystem health', 'Pipeline KPIs', 'Channel analytics', 'Sector intelligence'],
    statRender: (s) => (
      <>
        <LiveStat label="trend analyses" value={s?.strategist?.trend_analyses_count} />
        <LiveStat label="board briefs generated" value={s?.strategist?.board_briefs_generated} />
      </>
    ),
  },
];

/* ------------------------------------------------------------------ */
/*  Page component                                                     */
/* ------------------------------------------------------------------ */
export default function AITeam() {
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await api.get('/api/v1/ai-team/stats');
        if (!cancelled) setStats(res.data);
      } catch (err) {
        console.error('Failed to load AI team stats', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="font-heading text-3xl md:text-4xl text-ink mb-3">
          {t('ai_team.title')}
        </h1>
        <p className="text-ink/60 max-w-2xl mx-auto leading-relaxed text-sm md:text-base">
          {t('ai_team.subtitle')}
        </p>
        <p className="mt-3 text-xs font-semibold tracking-widest uppercase text-teal/80">
          {t('ai_team.tagline')}
        </p>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-teal" />
        </div>
      )}

      {/* Agent grid */}
      {!loading && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
            {AGENTS.map((agent) => (
              <AgentCard key={agent.name} agent={agent} stats={stats} />
            ))}
          </div>

          {/* Team Philosophy */}
          <div className="bg-white rounded-xl shadow-md p-8 mb-8 border-l-4 border-teal">
            <h2 className="font-heading text-xl text-teal mb-3">{t('ai_team.philosophy_title')}</h2>
            <p className="text-ink/70 leading-relaxed text-sm">
              {t('ai_team.philosophy_body')}
            </p>
          </div>

          {/* Footer */}
          <div className="text-center text-xs text-ink/40 pb-6 space-y-1">
            <p className="font-semibold tracking-wide">
              {t('ai_team.footer_sigma')}
            </p>
            <p>{t('ai_team.footer_built')}</p>
          </div>
        </>
      )}
    </div>
  );
}
