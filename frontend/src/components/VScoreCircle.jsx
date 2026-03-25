import React, { useEffect, useState } from 'react';

const VSCORE_TIER_COLORS = {
  platinum: '#0D9488',
  gold: '#B8904A',
  silver: '#3B82F6',
  bronze: '#F59E0B',
  under_review: '#EF4444',
};

const VSCORE_TIER_LABELS = {
  platinum: 'Platinum',
  gold: 'Gold',
  silver: 'Silver',
  bronze: 'Bronze',
  under_review: 'Under Review',
};

const REP_TIER_COLORS = {
  trusted: '#10B981',
  established: '#0D9488',
  emerging: '#F59E0B',
  new: '#94A3B8',
  flagged: '#EF4444',
};

const REP_TIER_LABELS = {
  trusted: 'Trusted',
  established: 'Established',
  emerging: 'Emerging',
  new: 'New',
  flagged: 'Flagged',
};

const VScoreCircle = ({ score, tier, size = 56, legacy = false }) => {
  const [animatedScore, setAnimatedScore] = useState(legacy ? 0 : 300);

  const tierColors = legacy ? REP_TIER_COLORS : VSCORE_TIER_COLORS;
  const tierLabels = legacy ? REP_TIER_LABELS : VSCORE_TIER_LABELS;
  const color = tierColors[tier] || '#94A3B8';
  const maxScore = legacy ? 100 : 900;
  const minScore = legacy ? 0 : 300;
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const normalizedProgress = (animatedScore - minScore) / (maxScore - minScore);
  const progress = normalizedProgress * circumference;
  const strokeWidth = size > 48 ? 5 : 4;

  useEffect(() => {
    if (score == null) return;
    const start = legacy ? 0 : 300;
    const duration = 800;
    const startTime = performance.now();
    const animate = (now) => {
      const elapsed = now - startTime;
      const pct = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - pct, 3);
      setAnimatedScore(Math.round(start + eased * (score - start)));
      if (pct < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [score, legacy]);

  if (score == null) return null;

  return (
    <div className="flex flex-col items-center gap-0.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="currentColor" className="text-gray-700"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={color} strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - Math.max(0, progress)}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-bold text-white" style={{ fontSize: size > 48 ? '0.8rem' : '0.6rem' }}>
            {animatedScore}
          </span>
        </div>
      </div>
      <span
        className="text-xs font-semibold px-1.5 py-0.5 rounded-full whitespace-nowrap"
        style={{ backgroundColor: `${color}20`, color, fontSize: '0.6rem' }}
      >
        {tierLabels[tier] || tier}
      </span>
    </div>
  );
};

export default VScoreCircle;
