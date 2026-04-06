import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { config } from '../config';

const apiBase = config.apiUrl || '';
const isPublicApply = () => window.location.pathname === '/apply';

const COUNTRIES = ['UAE', 'Saudi Arabia', 'Egypt', 'India', 'UK', 'Netherlands', 'Other'];
const EMPLOYEE_COUNTS = ['1-10', '11-50', '51-200', '201-500', '500+'];
const DATA_RESIDENCY = ['UAE', 'EU', 'US', 'Other'];
const CERT_OPTIONS = ['ISO 27001', 'ISO 27017', 'SOC 2 Type II', 'CSA STAR', 'ISO 9001', 'ISO 42001', 'Other'];

const STEPS = ['Company Information', 'Contact Person', 'Compliance & Certifications', 'About Your Company'];

const SectionHeader = ({ number, title }) => (
  <div className="flex items-center gap-3 mb-6">
    <div className="w-8 h-8 rounded-full bg-[#C8A951] text-white flex items-center justify-center text-sm font-bold">{number}</div>
    <h2 className="font-heading text-xl text-[#1A3A4A]">{title}</h2>
  </div>
);

const ProgressBar = ({ current, total }) => (
  <div className="mb-8">
    <div className="flex justify-between mb-2">
      {STEPS.map((step, i) => (
        <div key={step} className={`text-xs font-medium ${i <= current ? 'text-[#C8A951]' : 'text-gray-400'}`}>
          {step}
        </div>
      ))}
    </div>
    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
      <div
        className="h-full bg-gradient-to-r from-[#C8A951] to-[#E8D48B] rounded-full transition-all duration-500"
        style={{ width: `${((current + 1) / total) * 100}%` }}
      />
    </div>
  </div>
);

const VendorOnboard = () => {
  const { token } = useParams();
  const publicMode = isPublicApply() || !token;
  const navigate = useNavigate();
  const [invite, setInvite] = useState(null);
  const [loadError, setLoadError] = useState('');
  const [loading, setLoading] = useState(!publicMode);
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [sectors, setSectors] = useState([]);

  // Form fields
  const [companyName, setCompanyName] = useState('');
  const [country, setCountry] = useState('UAE');
  const [sector, setSector] = useState('');
  const [website, setWebsite] = useState('');
  const [yearEstablished, setYearEstablished] = useState('');
  const [employeeCount, setEmployeeCount] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [descCertified, setDescCertified] = useState(false);
  const [certifications, setCertifications] = useState([]);
  const [dataResidency, setDataResidency] = useState('UAE');
  const [govWork, setGovWork] = useState(false);
  const [govWorkDesc, setGovWorkDesc] = useState('');
  const [briefDesc, setBriefDesc] = useState('');

  // Fetch sectors for public apply mode
  useEffect(() => {
    if (!publicMode) return;
    axios.get(`${apiBase}/api/v1/business-groups`)
      .then((res) => setSectors(res.data.business_groups || []))
      .catch(() => {});
  }, [publicMode]);

  useEffect(() => {
    if (publicMode) return; // no token to validate
    const fetchInvite = async () => {
      try {
        const res = await axios.get(`${apiBase}/api/v1/vendors/onboard/${token}`);
        setInvite(res.data);
        setCompanyName(res.data.vendor_name || '');
        setContactEmail(res.data.vendor_email || '');
        setSector(res.data.sector || '');
      } catch (e) {
        setLoadError(
          e.response?.data?.detail?.detail ||
          e.response?.data?.detail ||
          'This invitation link is invalid or has expired. Please contact the Chamber for a new invitation.'
        );
      } finally {
        setLoading(false);
      }
    };
    fetchInvite();
  }, [token, publicMode]);

  const toggleCert = (cert) => {
    setCertifications((prev) =>
      prev.includes(cert) ? prev.filter((c) => c !== cert) : [...prev, cert]
    );
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setSubmitError('');
    try {
      const payload = {
        company_name: companyName,
        country,
        sector,
        website: website || null,
        contact_name: contactName,
        contact_email: contactEmail,
        contact_phone: contactPhone || null,
        password,
        year_established: yearEstablished ? parseInt(yearEstablished, 10) : null,
        employee_count: employeeCount || null,
        desc_certified: descCertified,
        certifications: certifications.length > 0 ? certifications.join(', ') : null,
        previous_government_work: govWork ? (govWorkDesc || 'Yes') : null,
        data_residency_country: dataResidency,
        brief_description: briefDesc || null,
      };
      const url = publicMode
        ? `${apiBase}/api/v1/vendors/apply`
        : `${apiBase}/api/v1/vendors/onboard/${token}`;
      await axios.post(url, payload);
      setSuccess(true);
    } catch (e) {
      setSubmitError(
        e.response?.data?.detail?.detail ||
        e.response?.data?.detail ||
        'Failed to complete onboarding. Please try again.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const canProceed = () => {
    if (step === 0) return companyName && country && sector;
    if (step === 1) return contactName && contactEmail && password.length >= 8 && password === confirmPassword;
    return true;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FAF8F4] flex items-center justify-center">
        <div className="animate-pulse text-[#1A3A4A] font-heading text-2xl">Loading...</div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="min-h-screen bg-[#FAF8F4] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <h2 className="font-heading text-2xl text-[#1A3A4A] mb-2">Invalid Invitation</h2>
          <p className="text-gray-600">{loadError}</p>
        </div>
        <Footer />
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-[#FAF8F4] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-100 flex items-center justify-center">
            <svg className="w-8 h-8 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
          </div>
          <h2 className="font-heading text-2xl text-[#1A3A4A] mb-2">Welcome to AI Smart Sourcing!</h2>
          <p className="text-gray-600 mb-4">Your account has been created. You can log in now with your email and password.</p>
          <button onClick={() => navigate('/login')}
            className="px-6 py-2.5 rounded-lg bg-[#C8A951] text-white text-sm font-bold hover:bg-[#B8993F] transition">
            Go to Login
          </button>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF8F4]">
      {/* Header */}
      <header className="bg-gradient-to-r from-[#1A3A4A] to-[#2A5A6A] py-6 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="font-heading text-3xl text-white mb-1">
            {publicMode ? 'AI Smart Sourcing — Vendor Application' : 'AI Smart Sourcing'}
          </h1>
          <p className="text-[#C8A951] text-lg font-medium">
            {publicMode ? 'Apply to join the Dubai Chambers sourcing platform' : 'Vendor Onboarding'}
          </p>
          {!publicMode && (
            <p className="text-white/70 text-sm mt-1">You've been invited to join the Dubai Chambers sourcing platform</p>
          )}
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        <ProgressBar current={step} total={STEPS.length} />

        <div className="bg-white rounded-2xl shadow-lg p-6 md:p-8">
          {/* Section 1 — Company Information */}
          {step === 0 && (
            <div>
              <SectionHeader number={1} title="Company Information" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company Name {publicMode ? '*' : ''}</label>
                  {publicMode ? (
                    <input type="text" value={companyName} onChange={(e) => setCompanyName(e.target.value)}
                      placeholder="Your company name"
                      className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951]" />
                  ) : (
                    <input type="text" value={companyName} readOnly
                      className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm bg-gray-50 text-gray-500" />
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Country *</label>
                  <select value={country} onChange={(e) => setCountry(e.target.value)}
                    className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951] bg-white">
                    {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sector {publicMode ? '*' : ''}</label>
                  {publicMode ? (
                    <select value={sector} onChange={(e) => setSector(e.target.value)}
                      className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951] bg-white">
                      <option value="">Select a sector...</option>
                      {sectors.map((s) => <option key={s.name} value={s.name}>{s.name}</option>)}
                    </select>
                  ) : (
                    <input type="text" value={sector} readOnly
                      className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm bg-gray-50 text-gray-500" />
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Website URL</label>
                  <input type="url" value={website} onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://www.example.com"
                    className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951]" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Year Established</label>
                  <input type="number" value={yearEstablished} onChange={(e) => setYearEstablished(e.target.value)}
                    placeholder="e.g. 2015" min="1900" max="2026"
                    className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951]" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Number of Employees</label>
                  <select value={employeeCount} onChange={(e) => setEmployeeCount(e.target.value)}
                    className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951] bg-white">
                    <option value="">Select...</option>
                    {EMPLOYEE_COUNTS.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Section 2 — Contact Person */}
          {step === 1 && (
            <div>
              <SectionHeader number={2} title="Contact Person" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                  <input type="text" value={contactName} onChange={(e) => setContactName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951]" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                  {publicMode ? (
                    <input type="email" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)}
                      placeholder="you@company.com"
                      className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951]" />
                  ) : (
                    <input type="email" value={contactEmail} readOnly
                      className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm bg-gray-50 text-gray-500" />
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input type="tel" value={contactPhone} onChange={(e) => setContactPhone(e.target.value)}
                    placeholder="+971 50 123 4567"
                    className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951]" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                  <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                    placeholder="Create a password"
                    className={`w-full border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951] ${password && password.length < 8 ? 'border-red-300' : 'border-gray-200'}`} />
                  <p className="text-xs text-gray-400 mt-1">Minimum 8 characters</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password *</label>
                  <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm your password"
                    className={`w-full border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951] ${confirmPassword && password !== confirmPassword ? 'border-red-300' : 'border-gray-200'}`} />
                  {confirmPassword && password !== confirmPassword && (
                    <p className="text-xs text-red-500 mt-1">Passwords must match</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Section 3 — Compliance & Certifications */}
          {step === 2 && (
            <div>
              <SectionHeader number={3} title="Compliance & Certifications" />
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Are you DESC Certified?</label>
                  <div className="flex items-center gap-4">
                    <button type="button" onClick={() => setDescCertified(true)}
                      className={`px-6 py-2 rounded-lg text-sm font-medium transition ${descCertified ? 'bg-[#C8A951] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                      Yes
                    </button>
                    <button type="button" onClick={() => setDescCertified(false)}
                      className={`px-6 py-2 rounded-lg text-sm font-medium transition ${!descCertified ? 'bg-[#C8A951] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                      No
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Certifications Held</label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {CERT_OPTIONS.map((cert) => (
                      <label key={cert} className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                        <input type="checkbox" checked={certifications.includes(cert)} onChange={() => toggleCert(cert)}
                          className="w-4 h-4 rounded border-gray-300 text-[#C8A951] focus:ring-[#C8A951]" />
                        <span className="text-sm text-gray-700">{cert}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Data Residency — Where is your data hosted?</label>
                  <select value={dataResidency} onChange={(e) => setDataResidency(e.target.value)}
                    className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951] bg-white">
                    {DATA_RESIDENCY.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Have you previously worked with UAE government entities?</label>
                  <div className="flex items-center gap-4">
                    <button type="button" onClick={() => setGovWork(true)}
                      className={`px-6 py-2 rounded-lg text-sm font-medium transition ${govWork ? 'bg-[#C8A951] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                      Yes
                    </button>
                    <button type="button" onClick={() => setGovWork(false)}
                      className={`px-6 py-2 rounded-lg text-sm font-medium transition ${!govWork ? 'bg-[#C8A951] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                      No
                    </button>
                  </div>
                  {govWork && (
                    <textarea value={govWorkDesc} onChange={(e) => setGovWorkDesc(e.target.value)}
                      placeholder="Brief description of your government work experience..."
                      rows={3}
                      className="mt-3 w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951] resize-none" />
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Section 4 — About Your Company */}
          {step === 3 && (
            <div>
              <SectionHeader number={4} title="About Your Company" />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Brief description of your company and offerings
                </label>
                <textarea value={briefDesc} onChange={(e) => setBriefDesc(e.target.value.slice(0, 500))}
                  placeholder="Tell us about your company, products, and services..."
                  rows={6}
                  className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#C8A951] resize-none" />
                <p className="text-xs text-gray-400 mt-1 text-right">{briefDesc.length}/500</p>
              </div>
            </div>
          )}

          {submitError && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-red-600 text-sm">{submitError}</p>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-6 border-t border-gray-100">
            {step > 0 ? (
              <button onClick={() => setStep(step - 1)}
                className="px-6 py-2.5 rounded-lg border border-gray-200 text-gray-600 text-sm font-medium hover:bg-gray-50 transition">
                Back
              </button>
            ) : <div />}

            {step < STEPS.length - 1 ? (
              <button onClick={() => setStep(step + 1)} disabled={!canProceed()}
                className="px-6 py-2.5 rounded-lg bg-[#1A3A4A] text-white text-sm font-medium hover:bg-[#1A3A4A]/90 transition disabled:opacity-50">
                Continue
              </button>
            ) : (
              <button onClick={handleSubmit} disabled={submitting || !canProceed()}
                className="px-8 py-2.5 rounded-lg bg-[#C8A951] text-white text-sm font-bold hover:bg-[#B8993F] transition disabled:opacity-50">
                {submitting ? 'Submitting...' : publicMode ? 'Submit Application' : 'Complete Onboarding'}
              </button>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

const Footer = () => (
  <footer className="py-6 text-center">
    <p className="text-sm text-gray-400">
      Powered by <span className="font-semibold text-[#C8A951]">&sigma;I</span> — Added Intelligence
    </p>
  </footer>
);

export default VendorOnboard;
