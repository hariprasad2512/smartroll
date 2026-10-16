import React, { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { ArrowLeft, Clock3, Radio } from 'lucide-react';
import { api } from '../lib/api';

export default function ClassroomDisplay({ sessionId }) {
  const [session, setSession] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let mounted = true;
    const refresh = async () => {
      try { const data = await api(`/api/faculty/sessions/${sessionId}/display`); if (mounted) { setSession(data); setError(''); } }
      catch (err) { if (mounted) setError(err.message); }
    };
    refresh();
    const timer = window.setInterval(refresh, 1000);
    return () => { mounted = false; clearInterval(timer); };
  }, [sessionId]);

  if (!session) return <main className="display-page"><p>{error || 'Loading classroom display…'}</p><a href="/faculty">Back to faculty</a></main>;
  if (!session.is_active) return <main className="display-page"><a className="display-back" href="/faculty"><ArrowLeft size={16} />Faculty dashboard</a><section className="display-ended"><span className="eyebrow">Class session ended</span><h1>{session.title}</h1><p>Students can no longer check in to this session.</p><a className="button button-primary" href="/faculty">Return to attendance</a></section></main>;
  const checkIn = new URL('/check-in', window.location.origin);
  checkIn.searchParams.set('session', session.session_id);
  checkIn.hash = new URLSearchParams({ code: session.totp_code }).toString();
  const percent = Math.max(0, Math.min(100, (session.time_remaining / session.interval) * 100));
  return <main className="display-page">
    <a className="display-back" href="/faculty"><ArrowLeft size={16} />Faculty dashboard</a>
    <div className="display-status"><i className="status-dot live" /><span>Class in progress</span><span className="display-separator">·</span><span>{session.title}</span></div>
    <section className="display-content">
      <div className="display-qr"><QRCodeSVG value={checkIn.toString()} size={360} level="M" includeMargin /></div>
      <h1>Scan to check in</h1>
      <p className="display-help">Open your phone camera and scan this code. Sign in with Google to confirm attendance.</p>
      <div className="display-code-label">Or enter this code after signing in</div>
      <div className="display-code">{session.totp_code.slice(0, 3)} {session.totp_code.slice(3)}</div>
      <div className="display-countdown"><Clock3 size={16} /> New code in {session.time_remaining} seconds</div>
      <div className="display-progress"><span style={{ width: `${percent}%` }} /></div>
    </section>
    <footer className="display-footer"><Radio size={15} /> QR code refreshes automatically</footer>
  </main>;
}
