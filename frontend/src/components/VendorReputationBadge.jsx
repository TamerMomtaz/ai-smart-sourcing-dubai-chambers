import React, { useEffect, useState } from 'react';

const TIER_COLORS = {
  trusted: '#10B981',
  established: '#0D9488',
  emerging: '#F59E0B',
  new: '#94A3B8',
  flagged: '#EF4444',
};

const TIER_LABELS = {
  trusted: 'Trusted',
  established: 'Established',
  emerging: 'Emerging',
  new: 'New',
  flagged: 'Flagged',
};

const ReputationGauge = ({ score, tier, size = 64 }) => {
  const [animatedScore, setAnimatedScore] = useState(0);
  const color = TIER_COLORS[tier] || TIER_COLORS.new;
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (animatedScore / 100) * circumference;
  const strokeWidth = size > 48 ? 5 : 4;

  useEffect(() => {
    if (score == null) return;
    let start = 0;
    const duration = 800;
    const startTime = performance.now();
    const animate = (now) => {
      const elapsed = now - startTime;
      const pct = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - pct, 3);
      setAnimatedScore(Math.round(eased * score));
      if (pct < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [score]);

  if (score == null) return null;

  return (
    <div className="flex flex-col items-center gap-0.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            className="text-gray-700"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-bold text-white" style={{ fontSize: size > 48 ? '1rem' : '0.7rem' }}>
            {animatedScore}
          </span>
        </div>
      </div>
      <span
        className="text-xs font-semibold px-1.5 py-0.5 rounded-full"
        style={{ backgroundColor: `${color}20`, color }}
      >
        {TIER_LABELS[tier] || tier}
      </span>
    </div>
  );
};

export { ReputationGauge, TIER_COLORS, TIER_LABELS };
export default ReputationGauge;
