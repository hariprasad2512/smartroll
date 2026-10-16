import React, { useEffect, useRef, useState } from 'react';

export default function GoogleSignIn({ onCredential }) {
  const buttonRef = useRef(null);
  const [error, setError] = useState('');
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  useEffect(() => {
    if (!clientId) {
      setError('Google sign-in is not configured for this deployment.');
      return undefined;
    }
    let mounted = true;
    let interval;
    const render = () => {
      const google = window.google;
      if (!google?.accounts?.id || !buttonRef.current) return false;
      google.accounts.id.initialize({
        client_id: clientId,
        callback: ({ credential }) => onCredential(credential),
      });
      google.accounts.id.renderButton(buttonRef.current, {
        theme: 'outline', size: 'large', shape: 'rectangular', text: 'continue_with', width: 320,
      });
      return true;
    };
    if (!render()) {
      interval = window.setInterval(() => {
        if (mounted && render()) window.clearInterval(interval);
      }, 150);
    }
    return () => { mounted = false; window.clearInterval(interval); };
  }, [clientId, onCredential]);

  return <div className="google-signin-wrap">
    <div className="google-signin-button" ref={buttonRef} />
    {error && <p className="feedback error" role="alert">{error}</p>}
  </div>;
}
