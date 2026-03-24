import React, { useState, useEffect } from 'react';

const themes = [
  { id: 'teal', color: '#0D9488', label: 'T' },
  { id: 'gold', color: '#B8904A', label: 'G' },
  { id: 'blue', color: '#3B82F6', label: 'B' },
  { id: 'emerald', color: '#10B981', label: 'E' },
];

function ThemeSwitcher() {
  const [active, setActive] = useState(
    localStorage.getItem('theme') || 'teal'
  );

  const switchTheme = (themeId) => {
    document.documentElement.setAttribute('data-theme', themeId);
    localStorage.setItem('theme', themeId);
    setActive(themeId);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', active);
  }, []);

  return (
    <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', padding: '8px 0' }}>
      {themes.map(t => (
        <button
          key={t.id}
          onClick={() => switchTheme(t.id)}
          title={t.id.charAt(0).toUpperCase() + t.id.slice(1)}
          style={{
            width: 24,
            height: 24,
            borderRadius: '50%',
            backgroundColor: t.color,
            border: active === t.id ? '2px solid white' : '2px solid transparent',
            boxShadow: active === t.id ? '0 0 0 2px ' + t.color : 'none',
            cursor: 'pointer',
            outline: 'none',
            padding: 0,
          }}
        />
      ))}
    </div>
  );
}

export default ThemeSwitcher;
