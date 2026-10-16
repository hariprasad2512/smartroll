import React, { useCallback, useEffect, useState } from 'react';
import { ArrowUpRight, Clock3, LogOut, Play, Radio, RotateCcw, Users, X } from 'lucide-react';
import { api } from '../lib/api';

function Header({ user }) {
  const signOut = async () => {
    try { await api('/api/auth/logout', { method: 'POST' }); } catch { /* locally end the session */ }
    localStorage.removeItem('smartroll_access_token');
    window.location.assign('/sign-in?next=%2Ffaculty');
  };
  return <header className="topbar"><a className="brand" href="/faculty"><span className="brand-mark">S</span><span>SmartRoll</span></a><div className="account-menu"><span className="account-name">{user.name}</span><button className="icon-button" onClick={signOut} aria-label="Sign out" title="Sign out"><LogOut size={17} /></button></div></header>;
}

export default function FacultyDashboard({ user }) {
  const [session, setSession] = useState(null);
  const [title, setTitle] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [accounts, setAccounts] = useState([]);
  const [intervalSeconds, setIntervalSeconds] = useState(60);
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);

  const refresh = useCallback(async () => {
    try { setSession((await api('/api/faculty/sessions/active')).session); setError(''); }
    catch (err) { setError(err.message); }
  }, []);
  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => clearInterval(timer);
  }, [refresh]);

  const refreshAccounts = useCallback(async () => {
    try { setAccounts((await api('/api/faculty/students')).students); } catch { /* Faculty can still take attendance. */ }
  }, []);
  useEffect(() => { refreshAccounts(); }, [refreshAccounts]);

  const startSession = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const data = await api('/api/faculty/sessions', { method: 'POST', body: JSON.stringify({ title: title.trim() || 'Class session', interval_seconds: Number(intervalSeconds) }) });
      setTitle('');
      window.location.assign(`/faculty/display/${data.session_id}`);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const students = session?.students || [];
  const endSession = async () => {
    if (!session || !window.confirm('End this class session? Students will no longer be able to check in.')) return;
    try { await api(`/api/faculty/sessions/${session.session_id}/end`, { method: 'POST' }); await refresh(); }
    catch (err) { setError(err.message); }
  };
  const resetDevice = async (account) => {
    if (!window.confirm(`Reset the registered device for ${account.name}? Their current sign-in will be revoked.`)) return;
    try { await api(`/api/faculty/students/${account.identity_id}/reset-device`, { method: 'POST' }); await refreshAccounts(); }
    catch (err) { setError(err.message); }
  };
  const openProfile = async (identityId) => {
    setProfileLoading(true);
    setProfile({ loading: true });
    try { setProfile(await api(`/api/faculty/students/${identityId}`)); }
    catch (err) { setProfile({ error: err.message }); }
    finally { setProfileLoading(false); }
  };
  return <div className="app-shell">
    <Header user={user} />
    <main className="page">
      <div className="page-header faculty-page-header"><div><span className="eyebrow">Faculty workspace</span><h1>Attendance</h1><p>Start a class and follow check-ins as they arrive.</p></div>
        <form className="start-session-form" onSubmit={startSession}><input className="text-input session-title-input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Class or subject" aria-label="Class or subject" /><label className="interval-select-label">QR refresh<select className="text-input interval-select" value={intervalSeconds} onChange={(e) => setIntervalSeconds(e.target.value)} aria-label="QR refresh interval"><option value="30">30 sec</option><option value="60">60 sec · Default</option><option value="90">90 sec</option><option value="120">120 sec</option></select></label><button className="button button-primary" disabled={busy}><Play size={15} />{busy ? 'Starting…' : 'Start class'}</button></form>
      </div>
      {error && <div className="error-state" role="alert">{error}</div>}
      {!session ? <section className="card faculty-empty"><div className="empty-mark"><Radio size={22} /></div><h2>No active class</h2><p>Start a class to create a check-in code for students.</p></section> : <>
        <section className="card faculty-session-summary"><div><span className="eyebrow">Active class</span><h2>{session.title}</h2><span className="session-status"><i className="status-dot live" />In progress</span></div><div className="faculty-session-actions"><a className="button button-secondary" href={`/faculty/display/${session.session_id}`}>Open classroom display <ArrowUpRight size={15} /></a><button className="button button-secondary" onClick={endSession}><X size={15} />End class</button></div></section>
        <section className="card faculty-roster"><div className="roster-head"><div><span className="eyebrow">Live roster</span><h2 className="card-title">Students present</h2></div><span className="roster-count"><Users size={14} /> {students.length} present</span></div>
          {!students.length ? <div className="empty-state"><p>Waiting for the first check-in</p></div> : <div className="roster-list">{students.map((student) => <button className="roster-row roster-row-button" key={student.id} onClick={() => student.google_identity_id && openProfile(student.google_identity_id)}><span className="student-avatar">{student.student_name?.slice(0, 1).toUpperCase()}</span><span className="student-meta"><strong>{student.student_name}</strong><span>{student.enrollment_id}</span></span><time className="attendance-time"><Clock3 size={13} />{student.timestamp ? new Date(student.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}</time></button>)}</div>}
        </section>
      </>}
      <details className="card device-management"><summary><span><span className="eyebrow">Account recovery</span><strong>Student device registrations</strong></span><span className="roster-count">{accounts.length} accounts</span></summary><div className="device-list">{accounts.length ? accounts.map((account) => <div className="device-row" key={account.identity_id}><button className="student-meta student-profile-link" onClick={() => openProfile(account.identity_id)}><strong>{account.name}</strong><span>{account.enrollment_id || 'Enrollment ID pending'}</span></button><span className={`device-state ${account.device_registered ? 'registered' : ''}`}>{account.device_registered ? 'Device registered' : 'Reset · ready to register'}</span>{account.device_registered && <button className="button button-secondary device-reset" onClick={() => resetDevice(account)}><RotateCcw size={14} />Reset</button>}</div>) : <div className="empty-state"><p>No student accounts yet</p></div>}</div></details>
    </main>
    {profile && <div className="student-profile-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setProfile(null); }}><section className="card student-profile" role="dialog" aria-modal="true" aria-labelledby="student-profile-title"><button className="icon-button student-profile-close" onClick={() => setProfile(null)} aria-label="Close profile"><X size={18} /></button>{profileLoading || profile.loading ? <p>Loading student profile…</p> : profile.error ? <div className="error-state">{profile.error}</div> : <><span className="eyebrow">Student profile</span><h2 id="student-profile-title">{profile.student.name}</h2><p className="profile-enrollment">Enrollment ID · {profile.student.enrollment_id || 'Not set'}</p><div className="profile-attendance-total"><strong>{profile.student.classes_attended}</strong><span>classes attended with you</span></div><h3>Attendance history</h3>{profile.attendance.length ? <ul className="profile-attendance-list">{profile.attendance.map((record) => <li key={record.session_id}><span><strong>{record.class_name}</strong><small>{record.timestamp ? new Date(record.timestamp).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Time unavailable'}</small></span></li>)}</ul> : <p className="profile-empty">No attendance records for your classes yet.</p>}</>}</section></div>}
    <footer className="site-footer"><span>SmartRoll</span><span>Faculty workspace</span></footer>
  </div>;
}
