import { useState, useEffect, useRef } from 'react';
import { config } from '../config';

function useCountUp(target, duration = 1500) {
  const [value, setValue] = useState(0);
  const rafRef = useRef(null);

  useEffect(() => {
    if (target == null || target === 0) { setValue(0); return; }
    const start = performance.now();
    const from = 0;
    const tick = (now) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
      setValue(from + (target - from) * eased);
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [target, duration]);

  return value;
}

function Stat({ value, suffix, label, prefix, decimals = 0 }) {
  const animated = useCountUp(value);
  const display = animated != null
    ? `${prefix || ''}${decimals ? animated.toFixed(decimals) : Math.round(animated)}${suffix || ''}`
    : '—';

  return (
    <span style={{ whiteSpace: 'nowrap' }}>
      <span style={{ color: '#0D9488', fontFamily: 'monospace', fontWeight: 600 }}>
        {display}
      </span>{' '}
      <span>{label}</span>
    </span>
  );
}

export default function LivePulseBanner() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const base = config.apiUrl || '';
    fetch(`${base}/api/v1/public/stats`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setStats(data); })
      .catch(() => null);
  }, []);

  if (!stats) return null;

  return (
    <div style={{
      background: '#0F172A',
      borderRadius: '10px',
      padding: '14px 24px',
      marginBottom: '20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '6px',
      flexWrap: 'wrap',
      fontSize: '13px',
      color: '#94A3B8',
      letterSpacing: '0.2px',
    }}>
      <Stat value={stats.evaluated} suffix="" label="proposals evaluated" />
      <span style={{ color: '#334155' }}>|</span>
      <Stat value={stats.speed_multiplier} suffix="x" label="faster" />
      <span style={{ color: '#334155' }}>|</span>
      <Stat value={stats.total_cost_usd} prefix="$" label="AI cost" decimals={2} />
      <span style={{ color: '#334155' }}>|</span>
      <Stat value={stats.shield_checks} suffix="" label="shield checks" />
    </div>
  );
}
