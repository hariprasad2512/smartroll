import React, { useEffect, useMemo, useState } from 'react';
import { ArrowRight, CheckCircle2, Clock3, QrCode } from 'lucide-react';
import { api, currentPath } from '../lib/api';

export default function StudentCheckIn() {
  const query = useMemo(() => new URLSearchParams(window.location.search), []);
  const sessionId = Number(query.get('session'));
  const code = query.get('code') || new URLSearchParams(window.location.hash.slice(1)).get('code') || '';
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [done, setDone] = useState(false);

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
      setFeedback(result.message);
    } catch (err) { setFeedback(err.message); }
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
            {user.role !== 'student' ? <div className="error-state">This account is registered for faculty access.</div> : <button className="button button-primary checkin-submit" disabled={submitting || code.length !== 6}>{submitting ? 'Recording attendance…' : <>Confirm attendance <ArrowRight size={16} /></>}</button>}
          </form> : <button className="button button-primary checkin-submit" onClick={continueToSignIn}>Sign in with Google <ArrowRight size={16} /></button>}
          <p className="checkin-note"><Clock3 size={13} /> This code expires shortly. Scan the classroom display again if it expires.</p></>}
        </>}
      </>}
    </section>
    <footer className="auth-footer">Attendance confirmation</footer>
  </main>;
}
