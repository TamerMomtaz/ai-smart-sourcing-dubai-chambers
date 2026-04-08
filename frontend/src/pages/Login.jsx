import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { useTranslation } from '../lib/language';
import { getErrorMessage } from '../lib/api';
import LivePulseBanner from '../components/LivePulseBanner';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { signIn, user } = useAuth();
  const { t } = useTranslation();

  const expired = searchParams.get('expired') === 'true';

  useEffect(() => {
    if (user) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    if (expired) {
      setError(t('auth.session_expired'));
    }
  }, [expired]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { error: signInError } = await signIn(email, password);
      if (signInError) {
        setError(signInError);
      } else {
        navigate('/dashboard', { replace: true });
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="font-heading text-4xl text-teal mb-2">{t('app.title')}</h1>
          <p className="font-body text-ink/70">{t('app.subtitle')}</p>
        </div>

        <LivePulseBanner />

        <div className="bg-white rounded-xl shadow-md p-8">
          <h2 className="font-heading text-2xl text-ink mb-6">{t('auth.sign_in')}</h2>

          {error && (
            <div className="mb-4 p-3 bg-burgundy/10 border border-burgundy/20 rounded-lg">
              <p className="text-sm text-burgundy font-body">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-body text-ink mb-1">
                {t('auth.email')}
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-ink/20 rounded-lg font-body text-ink focus:outline-none focus:ring-2 focus:ring-teal focus:border-transparent"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-body text-ink mb-1">
                {t('auth.password')}
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-ink/20 rounded-lg font-body text-ink focus:outline-none focus:ring-2 focus:ring-teal focus:border-transparent"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal text-white font-body py-2 px-4 rounded-lg hover:bg-teal/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? t('auth.signing_in') : t('auth.sign_in')}
            </button>
          </form>

          <div className="mt-6 text-center space-y-2">
            <p className="text-sm font-body text-ink/70">
              {t('auth.no_account')}{' '}
              <Link to="/register" className="text-teal hover:underline">
                {t('auth.register_here')}
              </Link>
            </p>
            <p className="text-sm font-body text-ink/50">
              {t('auth.new_here')}{' '}
              <Link to="/how-it-works" className="text-teal hover:underline">
                {t('auth.see_how')} &rarr;
              </Link>
            </p>
            <p className="text-sm font-body text-ink/50">
              {t('auth.vendor_question')}{' '}
              <Link to="/apply" className="text-teal hover:underline">
                {t('auth.vendor_apply')} &rarr;
              </Link>
            </p>
          </div>
        </div>

        <p className="text-center text-sm font-body text-ink/50 mt-6">
          {t('app.built_by')}
        </p>
      </div>
    </div>
  );
}

export default Login;
