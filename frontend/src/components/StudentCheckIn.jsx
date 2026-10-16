import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight, Camera, CheckCircle2, Clock3, QrCode, X } from 'lucide-react';
import { Html5Qrcode } from 'html5-qrcode';
import { api, currentPath } from '../lib/api';

export default function StudentCheckIn() {
  const query = useMemo(() => new URLSearchParams(window.location.search), []);
  const sessionId = Number(query.get('session'));
  const initialCode = query.get('code') || new URLSearchParams(window.location.hash.slice(1)).get('code') || '';
  const [code, setCode] = useState(initialCode);
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [done, setDone] = useState(false);
  const [expired, setExpired] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const scannerRef = useRef(null);
  const acceptedScanRef = useRef(false);

  useEffect(() => {
    let mounted = true;
    Promise.all([
      sessionId ? api(`/api/student/sessions/${sessionId}`) : Promise.reject(new Error('This QR code is missing its class session.')),
      localStorage.getItem('smartroll_access_token') ? api('/api/auth/me').catch(() => null) : Promise.resolve(null),
    ]).then(([sessionData, authData]) => {
      if (!mounted) return;
      setSession(sessionData);
      setUser(authData?.user || null);
      if (!sessionData.is_active) setFeedback('This class session has ended.');
    }).catch((err) => { if (mounted) setFeedback(err.message); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [sessionId]);

  const continueToSignIn = () => window.location.assign(`/sign-in?next=${encodeURIComponent(currentPath())}`);
  const signOutToLinkEnrollment = async () => {
    try { await api('/api/auth/logout', { method: 'POST' }); } catch { /* clear the local session either way */ }
    localStorage.removeItem('smartroll_access_token');
    window.location.assign(`/sign-in?next=${encodeURIComponent(currentPath())}`);
  };

  useEffect(() => {
    if (!cameraOpen) return undefined;
    acceptedScanRef.current = false;
    let mounted = true;
    const scanner = new Html5Qrcode('qr-recovery-reader');
    scannerRef.current = scanner;
    scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: { width: 240, height: 240 } },
      (decodedText) => {
        if (acceptedScanRef.current) return;
        try {
          const scanned = new URL(decodedText);
          const scannedCode = scanned.searchParams.get('code') || new URLSearchParams(scanned.hash.slice(1)).get('code');
          if (scanned.origin !== window.location.origin || scanned.pathname !== '/check-in' || Number(scanned.searchParams.get('session')) !== sessionId || !/^\d{6}$/.test(scannedCode || '')) {
            setCameraError('That QR code is not for this class. Scan the current code shown by your instructor.');
            return;
          }
          acceptedScanRef.current = true;
          setCode(scannedCode);
          setExpired(false);
          setFeedback('');
          setCameraError('');
          setCameraOpen(false);
        } catch {
          setCameraError('Could not read that QR code. Try again or enter the six-digit code.');
        }
      },
      () => {},
    ).catch((err) => {
      if (mounted) setCameraError(err?.message || 'Could not open the camera. Check browser camera permissions or enter the six-digit code.');
    });
    return () => {
      mounted = false;
      if (scannerRef.current === scanner) scannerRef.current = null;
      scanner.stop().then(() => scanner.clear()).catch(() => {});
    };
  }, [cameraOpen, sessionId]);

  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setFeedback('');
    try {
      const result = await api('/api/student/attendance', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId, totp_code: code }),
      });
      setDone(true);
      setExpired(false);
      setFeedback(result.message);
    } catch (err) {
      setFeedback(err.message);
      const codeExpired = err.message.toLowerCase().includes('expired');
      setExpired(codeExpired);
      if (codeExpired) setCode('');
    }
    finally { setSubmitting(false); }
  };

  return <main className="checkin-page">
    <a className="brand checkin-brand" href="/"><span className="brand-mark"><QrCode size={19} /></span><span>SmartRoll</span></a>
    <section className="card checkin-card">
      {loading ? <div className="empty-state"><p>Loading class…</p></div> : <>
        {done ? <div className="checkin-success-icon"><CheckCircle2 size={25} /></div> : <span className="eyebrow">Student check-in</span>}
        <h1>{done ? 'You’re checked in' : session?.title || 'Class check-in'}</h1>
        {done ? <p className="checkin-copy">{feedback}</p> : <>
          <p className="checkin-copy">{session?.is_active ? 'Your instructor has started this class. Sign in to confirm your attendance.' : 'This class session is no longer active.'}</p>
          {feedback && <div className="feedback error" role="alert">{feedback}</div>}
          {session?.is_active && <>{user ? <form onSubmit={submit}>
            <div className="signed-in-user"><span className="student-avatar">{user.name.slice(0, 1).toUpperCase()}</span><span><strong>{user.name}</strong><small>{user.email}</small></span></div>
            {user.role !== 'student' ? <div className="error-state">This account is registered for faculty access.</div> : !user.enrollment_id ? <div className="feedback error enrollment-relink"><span>This account needs an Enrollment ID before you can check in.</span><button className="button button-secondary" type="button" onClick={signOutToLinkEnrollment}>Sign out and add Enrollment ID</button></div> : <>
              {expired && <div className="code-recovery">
                <span className="eyebrow">Code expired</span>
                <p>Scan the classroom QR again or enter the new six-digit code shown on the display.</p>
                {!cameraOpen ? <button className="button button-secondary recovery-camera-button" type="button" onClick={() => { setCameraError(''); setCameraOpen(true); }}><Camera size={16} />Scan QR again</button> : <div className="camera-recovery"><div className="camera-recovery-head"><strong>Scan the classroom QR</strong><button className="icon-button" type="button" onClick={() => setCameraOpen(false)} aria-label="Close camera"><X size={17} /></button></div><div id="qr-recovery-reader" />{cameraError && <p className="camera-error" role="alert">{cameraError}</p>}</div>}
                <label className="manual-code-label">Or enter the new code<input className="text-input manual-code-input" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={code} onChange={(event) => { setCode(event.target.value.replace(/\D/g, '').slice(0, 6)); setFeedback(''); }} placeholder="000000" /></label>
              </div>}
              <button className="button button-primary checkin-submit" disabled={submitting || code.length !== 6 || cameraOpen}>{submitting ? 'Recording attendance…' : <>Confirm attendance <ArrowRight size={16} /></>}</button>
            </>}
          </form> : <button className="button button-primary checkin-submit" onClick={continueToSignIn}>Sign in with Google <ArrowRight size={16} /></button>}
          <p className="checkin-note"><Clock3 size={13} /> This code expires shortly. Scan the classroom display again if it expires.</p></>}
        </>}
      </>}
    </section>
    <footer className="auth-footer">Attendance confirmation</footer>
  </main>;
}
