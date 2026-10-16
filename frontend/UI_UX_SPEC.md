# SmartRoll UI / UX Specification

**Status:** Product baseline
**Purpose:** Shared reference for future interface changes. Layout, language, visual tokens, and behavior should follow this specification unless the product direction is deliberately revised.

## Product intent

SmartRoll helps instructors start a class attendance session and helps students check in from a phone. The interface should feel dependable, calm, clear, fast to scan, and usable in a bright room or on a small screen.

The product is organized around two jobs:

1. **Instructor:** display a rotating attendance QR code and passcode, see who checked in, and start a named session.
2. **Student:** identify themselves, scan or enter the current code, submit attendance, and receive a clear result.

Avoid decorative gradients, glow effects, novelty labels, unexplained metrics, and repeated instructions. Do not describe the product as a hackathon demo in the interface.

## Product structure

### Routes and page ownership

- `/sign-in`: Google account sign-in. Redirect to the page that requested authentication.
- `/faculty`: faculty dashboard with active class, live roster, class creation, and student device recovery.
- `/faculty/display/:sessionId`: projector layout containing only the class title, QR check-in link, rotating code, and expiry countdown.
- `/check-in?session=:id#code=:totp`: mobile check-in destination opened directly by a native camera or Lens.
- `/student`: signed-in student landing page with instructions for scanning the classroom display.
- Do not place faculty and student workspaces side by side or provide a client-side role switch.
- Faculty accounts are enabled only for emails in the server-side `FACULTY_EMAILS` allowlist. Any other verified Google account self-enrolls as a student.

### Faculty dashboard and classroom display

- Dashboard shows the active class, present count, newest check-ins, a class-name field, and **Start class** / **End class** actions.
- **Open classroom display** navigates to a separate projector page; the dashboard stays focused on roster and session management.
- The display has a large black-on-white QR code with an adequate quiet zone, six-digit fallback code, title, and expiry countdown. Do not show student names on the projector.
- QR encodes an HTTPS link to `/check-in` with the session ID and current TOTP in the URL fragment. The code stays client-side and is not sent in normal HTTP requests. Keep the QR useful to native camera apps.
- Empty, loading, expired-session, and service-error states must be distinct.

### Student check-in

- Scanning the class QR opens `/check-in` in a browser and carries a short-lived session code.
- The check-in page shows class name and Google identity. An unauthenticated student signs in and returns to the same session.
- Signed-in students confirm attendance with one explicit action; they do not re-enter name or ID.
- Submission disables repeat clicks and communicates progress. Success, duplicate, expired-code, inactive-session, device-conflict, and sign-in errors explain the next step.
- Google `sub` identifies the account. Email and display name are profile details, not unique identity keys.
- The first browser/device registration is bound to that Google account. Students changing devices must ask faculty to reset the registration.

## Visual system

- Warm near-white canvas, white surfaces, fine neutral borders, dark text, and one muted green accent.
- Prefer spacing and alignment over decorative containers.
- Use one-pixel borders and modest corner radii. Avoid shadows except for overlays.
- Use icons when they improve recognition; pair them with text for primary actions.
- Use monospaced numerals for codes and timestamps.

| Token | Value | Use |
| --- | --- | --- |
| Canvas | #f7f8f6 | Application background |
| Surface | #ffffff | Cards, header, fields |
| Text | #20231f | Main text |
| Muted text | #7b8179 | Supporting copy |
| Border | #e6e9e4 | Cards, separators, inputs |
| Accent | #3e6345 | Primary action and live progress |
| Success surface | #f0f6ef | Successful check-in |
| Error surface | #fff8f6 | Service and validation errors |
| Radius | 8–12 px | Controls and cards |

Typography uses DM Sans for interface text and DM Mono for codes. If web fonts cannot load, use system sans-serif and monospace fallbacks without layout failure.

## Interaction and realtime behavior

- QR payload and six-digit code rotate on the server's 30-second TOTP interval.
- Countdown is informational and resynchronizes with server data; it is not the source of token validity.
- Faculty roster refreshes from the API every three seconds; the projector code refreshes every second.
- Starting a session replaces the displayed code and roster with that session's data.
- On failed check-in, preserve entered identity and code so the student can correct or retry.

## Responsive and accessible behavior

- Desktop: wider QR/code panel beside a narrower attendance roster.
- Tablet and mobile: stack faculty controls; keep the projector QR large, centered, and high contrast.
- Student check-in uses one column and a single prominent confirmation action.
- Keep controls at least 40 px high. Do not rely on hover for important states.
- At 320 px width, sign-in, check-in, and faculty controls remain usable without horizontal overflow.
- Use semantic headings, associated input labels, buttons for actions, and status/live regions for asynchronous results.
- Provide visible keyboard focus, sufficient text contrast, and accessible names for icon-only controls.
- Do not communicate status by color alone. Include words such as “Live updates”, “Reconnecting”, “Present”, or explicit feedback.

## Failure and edge states

- **Service unavailable:** explain that the attendance service cannot be reached and retain form/session context.
- **No active session:** tell the student to wait for the instructor's code; allow QR scanning where possible.
- **Invalid or expired code:** ask the student to scan the current classroom display again.
- **Duplicate check-in:** show the API's existing attendance confirmation as a successful state.
- **Device conflict:** explain that the Google account is registered on another device and direct the student to faculty for reset.
- **Empty roster:** state that no one has checked in yet without implying a failure.

## Current product limits and follow-up

Google sign-in requires the same OAuth web client ID in `frontend/.env` (`VITE_GOOGLE_CLIENT_ID`) and `backend/.env` (`GOOGLE_CLIENT_ID`). Set comma-separated faculty emails in `backend/.env` (`FACULTY_EMAILS`). Add the frontend origin to the Google OAuth client's authorized JavaScript origins.

The device binding currently uses a persistent browser-generated device ID. It deters signing into the same Google account from another browser profile/device, but it is not hardware attestation and can be copied by a determined user. A short-lived QR can also be relayed live. Absolute proxy prevention cannot be guaranteed by a browser QR flow; this design is a deterrent and audit mechanism, not proof of physical presence.

The API issues a 12-hour bearer session stored by the frontend. Use HTTPS in production. Consider moving to secure, HTTP-only cookies and hardware-backed device credentials before treating attendance as high assurance.

## API endpoints

| Endpoint | Access | Purpose |
| --- | --- | --- |
| `POST /api/auth/google` | Public | Verify Google credential, self-enroll or sign in, bind device |
| `GET /api/auth/me` | Signed in | Current profile and role |
| `POST /api/auth/logout` | Signed in | Revoke current API session |
| `POST /api/faculty/sessions` | Faculty | Start a named class |
| `GET /api/faculty/sessions/active` | Faculty | Active class and attendance roster |
| `GET /api/faculty/sessions/{id}` | Owning faculty | Full class details and roster |
| `GET /api/faculty/sessions/{id}/display` | Owning faculty | Current rotating projector code |
| `POST /api/faculty/sessions/{id}/end` | Owning faculty | End check-in for a class |
| `GET /api/faculty/students` | Faculty | Self-enrolled student accounts and device state |
| `POST /api/faculty/students/{identity_id}/reset-device` | Faculty | Revoke sessions and allow device re-registration |
| `GET /api/student/sessions/{id}` | Public | Safe class title and active status for QR landing page |
| `POST /api/student/attendance` | Signed-in student | Validate current code and record attendance |

Production follow-up should define instructor authentication, class/course ownership, session lifecycle and closing, student identity provisioning, retention/export policy, rate limiting, deployment API configuration, and cross-worker event delivery. Do not add these concepts to the UI until corresponding product and API behavior exists.

## Change control

Treat this document as the default acceptance reference for UI/UX work. A deviation should update this spec in the same change and explain the product reason. New screens and states should specify their user, goal, entry point, loading/empty/error/success behavior, responsive layout, and accessibility behavior.
