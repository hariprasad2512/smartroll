import React from 'react';
import { QrCode, LogOut } from 'lucide-react';

export default function StudentHome({ user }) {
  const signOut = () => {
    localStorage.removeItem('smartroll_access_token');
    window.location.assign('/sign-in');
  };
  return <main className="student-home-page">
    <header className="student-home-header"><a className="brand" href="/student"><span className="brand-mark"><QrCode size={19} /></span><span>SmartRoll</span></a><button className="button button-secondary" onClick={signOut}><LogOut size={15} />Sign out</button></header>
    <section className="card student-home-card"><span className="eyebrow">Student account</span><h1>Hello, {user.name.split(' ')[0]}</h1><p>When your instructor starts a class, scan the classroom QR code with your phone camera. SmartRoll will open the check-in page for that class.</p><div className="student-home-account"><span className="student-avatar">{user.name.slice(0, 1).toUpperCase()}</span><span><strong>{user.name}</strong><small>{user.email}</small></span></div><p className="auth-footnote">This Google account is registered to this device. Ask faculty to reset the registration if you need to move devices.</p></section>
  </main>;
}
