import React, { useCallback, useState } from 'react';
import { QrCode } from 'lucide-react';
import GoogleSignIn from './GoogleSignIn';
import { safeNextPath, signInWithGoogle } from '../lib/api';

export default function SignInPage() {
  const [error, setError] = useState('');
  const [working, setWorking] = useState(false);
  const [enrollmentId, setEnrollmentId] = useState('');
  const next = safeNextPath();
  const handleCredential = useCallback(async (credential) => {
    setWorking(true);
    setError('');
    try {
      const user = await signInWithGoogle(credential, enrollmentId.trim());
      const target = next.startsWith('/faculty') && user.role !== 'faculty' ? '/student' : next;
      window.location.assign(target);
    } catch (err) {
      setError(err.message);
      setWorking(false);
    }
  }, [enrollmentId, next]);

  return <main className="auth-page">
    <a className="brand auth-brand" href="/faculty"><span className="brand-mark"><QrCode size={19} /></span><span>SmartRoll</span></a>
    <section className="card auth-card">
      <span className="eyebrow">Secure sign in</span>
      <h1>Continue with Google</h1>
      <p>Use your Google account to check in or manage a class. Students should enter their Enrollment ID to link it to their account.</p>
      {error && <div className="feedback error" role="alert">{error}</div>}
      {!working && <label className="enrollment-input-label">Enrollment ID <span>(faculty can leave this blank)</span><input className="text-input enrollment-input" value={enrollmentId} onChange={(event) => setEnrollmentId(event.target.value)} autoComplete="off" /></label>}
      {working ? <p className="signin-progress">Verifying your Google account…</p> : <GoogleSignIn onCredential={handleCredential} />}
      <p className="auth-footnote">One account can be registered on one device. To move devices, ask faculty to reset your registration.</p>
    </section>
    <footer className="auth-footer">SmartRoll · Attendance</footer>
  </main>;
}
