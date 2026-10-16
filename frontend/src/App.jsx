import React, { useEffect, useState } from 'react';
import FacultyDashboard from './components/FacultyDashboard';
import ClassroomDisplay from './components/ClassroomDisplay';
import StudentCheckIn from './components/StudentCheckIn';
import StudentHome from './components/StudentHome';
import SignInPage from './components/SignInPage';
import { api, currentPath } from './lib/api';

function Protected({ children, faculty = false, student = false }) {
  const [state, setState] = useState({ loading: true, user: null, error: '' });
  useEffect(() => {
    let mounted = true;
    api('/api/auth/me').then((data) => {
      if (mounted) setState({ loading: false, user: data.user, error: '' });
    }).catch((err) => {
      if (mounted) setState({ loading: false, user: null, error: err.message });
    });
    return () => { mounted = false; };
  }, []);
  useEffect(() => {
    if (!state.loading && !state.user) window.location.replace(`/sign-in?next=${encodeURIComponent(currentPath())}`);
    else if (!state.loading && faculty && state.user?.role !== 'faculty') window.location.replace('/student');
    else if (!state.loading && student && state.user?.role !== 'student') window.location.replace('/faculty');
  }, [state, faculty]);
  if (state.loading || !state.user) return <main className="auth-page"><p className="signin-progress">Checking your sign-in…</p></main>;
  return children(state.user);
}

function NotFound() {
  return <main className="auth-page"><section className="card auth-card"><span className="eyebrow">Page not found</span><h1>This page doesn’t exist</h1><p>Open the class QR code again or return to SmartRoll.</p><a className="button button-primary" href="/">Go to sign in</a></section></main>;
}

export default function App() {
  useEffect(() => { document.title = 'SmartRoll · Attendance'; }, []);
  const path = window.location.pathname;
  if (path === '/' || path === '/sign-in' || path === '/faculty/sign-in') return <SignInPage />;
  if (path === '/check-in') return <StudentCheckIn />;
  if (path === '/student') return <Protected student>{(user) => <StudentHome user={user} />}</Protected>;
  if (path === '/faculty') return <Protected faculty>{(user) => <FacultyDashboard user={user} />}</Protected>;
  const displayMatch = path.match(/^\/faculty\/display\/(\d+)$/);
  if (displayMatch) return <Protected faculty>{() => <ClassroomDisplay sessionId={displayMatch[1]} />}</Protected>;
  return <NotFound />;
}
