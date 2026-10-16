"""Create the SmartRoll product pitch PDF using only Python's standard library."""

from pathlib import Path
import re


OUT = Path(__file__).with_name("SmartRoll_Product_Brief.pdf")
NAVY = "172B3A"
GREEN = "3E6345"
MINT = "EAF1E8"
PAPER = "F7F8F6"
WHITE = "FFFFFF"
INK = "20231F"
MUTED = "68736B"
BORDER = "DCE3DC"
BLUE = "EAF1F7"
GOLD = "F6F0E1"
RED = "FAECE8"


def rgb(color):
    return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))


class Page:
    def __init__(self, width=612, height=792):
        self.width = width
        self.height = height
        self.ops = []

    def rect(self, x, y, w, h, fill=WHITE, stroke=None, radius=0):
        f = rgb(fill)
        self.ops.append(f"{f[0]:.3f} {f[1]:.3f} {f[2]:.3f} rg")
        if stroke:
            s = rgb(stroke)
            self.ops.append(f"{s[0]:.3f} {s[1]:.3f} {s[2]:.3f} RG 0.8 w")
        py = self.height - y - h
        if not radius:
            self.ops.append(f"{x:.1f} {py:.1f} {w:.1f} {h:.1f} re {'B' if stroke else 'f'}")
            return
        r = min(radius, w / 2, h / 2)
        k = 0.55228475
        p = [f"{x+r:.1f} {py+h:.1f} m", f"{x+w-r:.1f} {py+h:.1f} l",
             f"{x+w-r+k*r:.1f} {py+h:.1f} {x+w:.1f} {py+h-r+k*r:.1f} {x+w:.1f} {py+h-r:.1f} c",
             f"{x+w:.1f} {py+r:.1f} l", f"{x+w:.1f} {py+r-k*r:.1f} {x+w-r+k*r:.1f} {py:.1f} {x+w-r:.1f} {py:.1f} c",
             f"{x+r:.1f} {py:.1f} l", f"{x+r-k*r:.1f} {py:.1f} {x:.1f} {py+r-k*r:.1f} {x:.1f} {py+r:.1f} c",
             f"{x:.1f} {py+h-r:.1f} l", f"{x:.1f} {py+h-r+k*r:.1f} {x+r-k*r:.1f} {py+h:.1f} {x+r:.1f} {py+h:.1f} c", "h"]
        self.ops.extend(p)
        self.ops.append("B" if stroke else "f")

    def line(self, x1, y1, x2, y2, color=BORDER, width=1):
        c = rgb(color)
        self.ops.append(f"{c[0]:.3f} {c[1]:.3f} {c[2]:.3f} RG {width:.1f} w {x1:.1f} {self.height-y1:.1f} m {x2:.1f} {self.height-y2:.1f} l S")

    def arrow(self, points, color=GREEN, width=1.4, label=None, label_at=None):
        c = rgb(color)
        self.ops.append(f"{c[0]:.3f} {c[1]:.3f} {c[2]:.3f} RG {width:.1f} w")
        x0, y0 = points[0]
        self.ops.append(f"{x0:.1f} {self.height-y0:.1f} m")
        for x, y in points[1:]:
            self.ops.append(f"{x:.1f} {self.height-y:.1f} l")
        self.ops.append("S")
        x1, y1 = points[-2]
        x2, y2 = points[-1]
        import math
        angle = math.atan2(y2-y1, x2-x1)
        size = 6
        left = (x2-size*math.cos(angle-0.48), y2-size*math.sin(angle-0.48))
        right = (x2-size*math.cos(angle+0.48), y2-size*math.sin(angle+0.48))
        self.ops.append(f"{c[0]:.3f} {c[1]:.3f} {c[2]:.3f} rg {x2:.1f} {self.height-y2:.1f} m {left[0]:.1f} {self.height-left[1]:.1f} l {right[0]:.1f} {self.height-right[1]:.1f} l h f")
        if label and label_at:
            self.text(label_at[0], label_at[1], label, 8, color, True)

    def text(self, x, y, value, size=11, color=INK, bold=False):
        c = rgb(color)
        safe = value.encode("latin-1", "replace").decode("latin-1")
        safe = safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        font = "F2" if bold else "F1"
        py = self.height - y - size
        self.ops.append(f"BT /{font} {size:.1f} Tf {c[0]:.3f} {c[1]:.3f} {c[2]:.3f} rg 1 0 0 1 {x:.1f} {py:.1f} Tm ({safe}) Tj ET")

    def wrapped(self, x, y, text, max_width, size=10, color=MUTED, leading=None, bold=False):
        leading = leading or size * 1.42
        words = text.split()
        lines, current = [], ""
        max_chars = max(12, int(max_width / (size * (0.56 if bold else 0.52))))
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) > max_chars and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        for i, line in enumerate(lines):
            self.text(x, y + i * leading, line, size, color, bold)
        return y + len(lines) * leading

    def pill(self, x, y, label, fill=MINT, color=GREEN):
        w = max(58, len(label) * 5.8 + 18)
        self.rect(x, y, w, 20, fill, radius=8)
        self.text(x + 9, y + 5, label.upper(), 8, color, True)

    def card(self, x, y, w, h, title, body, tint=WHITE, tag=None):
        self.rect(x, y, w, h, tint, BORDER, 9)
        if tag:
            self.pill(x + 12, y + 11, tag, MINT, GREEN)
            self.text(x + 12, y + 41, title, 13, INK, True)
            self.wrapped(x + 12, y + 61, body, w - 24, 9, MUTED, 12)
        else:
            self.text(x + 13, y + 16, title, 12, INK, True)
            self.wrapped(x + 13, y + 37, body, w - 26, 9, MUTED, 12)

    def node(self, x, y, w, h, title, body=None, fill=WHITE, accent=GREEN, center=True):
        self.rect(x, y, w, h, fill, BORDER, 8)
        self.rect(x, y, 4, h, accent)
        if center:
            title_size = 9.3
            chars = max(12, int((w - 20) / (title_size * .53)))
            lines = wrap(title, chars)
            top = y + (h - len(lines) * 12 - (16 if body else 0)) / 2
            for i, line in enumerate(lines):
                self.text(x + 12, top + i * 12, line, title_size, INK, True)
            if body:
                self.wrapped(x + 12, top + len(lines) * 12 + 4, body, w - 23, 7.5, MUTED, 9)
        else:
            self.text(x + 12, y + 13, title, 9.3, INK, True)
            if body:
                self.wrapped(x + 12, y + 30, body, w - 22, 7.5, MUTED, 9)


def wrap(text, max_chars):
    result, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            result.append(current)
            current = word
        else:
            current = candidate
    if current:
        result.append(current)
    return result


def base_page(title, kicker, number, width=612, height=792):
    p = Page(width, height)
    p.rect(0, 0, width, height, PAPER)
    p.rect(0, 0, width, 9, GREEN)
    p.text(34, 24, "SMARTROLL", 9, GREEN, True)
    p.text(width - 125, 24, "PRODUCT BRIEF  /  OCT 2026", 7.4, MUTED, True)
    p.text(34, 53, kicker.upper(), 8, GREEN, True)
    p.text(34, 69, title, 22, INK, True)
    p.line(34, height - 33, width - 34, height - 33, BORDER, .8)
    p.text(34, height - 25, "SmartRoll  |  Attendance workflow and access model", 7.5, MUTED)
    p.text(width - 52, height - 25, str(number), 8, MUTED, True)
    return p


def cover():
    p = Page()
    p.rect(0, 0, 612, 792, PAPER)
    p.rect(0, 0, 612, 10, GREEN)
    p.text(40, 36, "SMARTROLL", 10, GREEN, True)
    p.text(446, 37, "PRODUCT PITCH  /  OCT 2026", 7.5, MUTED, True)
    p.pill(40, 100, "DIGITAL CLASS ATTENDANCE", MINT, GREEN)
    p.text(40, 142, "Attendance, without", 31, INK, True)
    p.text(40, 179, "the roll-call bottleneck.", 31, INK, True)
    p.wrapped(42, 226, "SmartRoll helps faculty run a class check-in from a live QR code while students confirm attendance on their phones. No student app install is needed.", 492, 12, MUTED, 18)
    p.rect(40, 292, 532, 90, NAVY, radius=12)
    p.text(61, 310, "THE CLASSROOM LOOP", 8, "BFD5C0", True)
    steps = [(61, "Faculty starts"), (190, "QR rotates"), (318, "Student scans"), (446, "Roster updates")]
    for idx, (x, label) in enumerate(steps):
        p.rect(x, 340, 105, 26, "263D4B", radius=7)
        p.text(x + 9, 348, label, 8.2, WHITE, True)
        if idx < len(steps) - 1:
            p.arrow([(x + 109, 353), (x + 124, 353)], "91B99A", 1.3)
    p.text(40, 418, "WHY IT FITS A CLASSROOM", 8, GREEN, True)
    p.card(40, 437, 164, 112, "Fast check-in", "A changing QR and six-digit fallback code let students check in from the room display.", WHITE)
    p.card(224, 437, 164, 112, "Clear ownership", "Faculty sees a live roster; each student account links to an Enrollment ID.", WHITE)
    p.card(408, 437, 164, 112, "Institution-ready", "The planned access model separates institutions, memberships, records, and administrators.", WHITE)
    p.text(40, 580, "DEPLOYMENT SHAPE", 8, GREEN, True)
    p.text(40, 602, "Cloudflare-hosted web app", 11, INK, True)
    p.text(242, 602, "Render API", 11, INK, True)
    p.text(383, 602, "Supabase PostgreSQL", 11, INK, True)
    p.arrow([(196, 611), (229, 611)], GREEN)
    p.arrow([(322, 611), (370, 611)], GREEN)
    p.text(40, 645, "Google Identity Services verifies accounts; the API authorizes roles and writes attendance records.", 8.8, MUTED)
    p.rect(40, 682, 532, 60, GOLD, radius=9)
    p.text(54, 695, "SCOPE NOTE", 8, "8A6B29", True)
    p.wrapped(54, 710, "Student and faculty workflows are in the current codebase. Global superadmin and institution-admin workflows are proposed next-phase work, not yet implemented.", 500, 8.2, INK, 11)
    return p


def flowchart():
    p = base_page("Role-based access flow", "Target multi-institution model", 2, 792, 612)
    # Authentication and access decisions
    p.node(32, 116, 112, 48, "Open SmartRoll", fill=WHITE)
    p.node(178, 116, 142, 48, "Google sign-in", "Verify identity", fill=BLUE, accent="50718A")
    p.node(364, 108, 126, 64, "Global superadmin?", fill=GOLD, accent="A98231")
    p.node(584, 88, 174, 62, "Global administration", "Create institutions; assign institution admins", fill=GOLD, accent="A98231")
    p.arrow([(144, 140), (178, 140)])
    p.arrow([(320, 140), (364, 140)])
    p.arrow([(490, 126), (584, 119)])
    p.text(523, 113, "YES", 7.5, GREEN, True)
    p.node(178, 208, 142, 52, "Select institution", "Use the active membership", fill=WHITE)
    p.node(364, 203, 126, 62, "Membership found?", fill=WHITE, accent="50718A")
    p.node(584, 207, 174, 52, "No membership", "Request invitation or enrollment", fill=RED, accent="A95743")
    p.arrow([(427, 172), (427, 187), (320, 187), (320, 234)])
    p.text(340, 185, "NO", 7.5, MUTED, True)
    p.arrow([(320, 234), (364, 234)])
    p.arrow([(490, 234), (584, 234)])
    p.text(523, 222, "NO", 7.5, "A95743", True)
    p.node(364, 296, 126, 62, "Role in institution?", fill=WHITE, accent="50718A")
    p.arrow([(427, 265), (427, 296)])
    p.text(438, 276, "YES", 7.5, GREEN, True)
    # Three role lanes
    p.node(32, 414, 210, 103, "Institution admin", "Manage this institution's faculty, students, device resets, settings, and audit log.", fill=BLUE, accent="50718A", center=False)
    p.node(291, 414, 210, 103, "Faculty", "Start class; choose 30 / 60 / 90 / 120 sec QR; view present students and class history.", fill=MINT, accent=GREEN, center=False)
    p.node(550, 414, 210, 103, "Student", "Link Google account to institution Enrollment ID; scan QR or enter the current code.", fill=WHITE, accent=GREEN, center=False)
    p.arrow([(394, 358), (394, 386), (137, 386), (137, 414)])
    p.text(237, 375, "INSTITUTION ADMIN", 7, "50718A", True)
    p.arrow([(427, 358), (427, 414)])
    p.text(437, 384, "FACULTY", 7, GREEN, True)
    p.arrow([(460, 358), (460, 386), (655, 386), (655, 414)])
    p.text(561, 375, "STUDENT", 7, GREEN, True)
    p.node(291, 536, 210, 42, "Live QR and roster", fill=WHITE, accent=GREEN)
    p.arrow([(396, 517), (396, 536)])
    p.node(550, 536, 210, 42, "Validate session and code", "Valid: record. Expired: rescan or enter new code.", fill=WHITE, accent=GREEN)
    p.arrow([(655, 517), (655, 536)])
    p.text(40, 545, "All data is institution-scoped.", 8.1, MUTED, True)
    return p


def workflows():
    p = base_page("How a class runs", "Faculty and student journeys", 3)
    p.wrapped(36, 111, "A faculty member creates a named session. The display keeps the room focused on one QR, one current code, and a clear countdown.", 530, 10, MUTED, 14)
    p.pill(36, 160, "FACULTY", MINT, GREEN)
    p.pill(316, 160, "STUDENT", BLUE, "50718A")
    left = [(36, 198, "1. Start a class", "Enter a class name and choose a refresh interval: 30, 60, 90, or 120 seconds. Default: 60 seconds."),
            (36, 292, "2. Project the code", "The classroom display shows a QR link and six-digit code. Both refresh on the selected interval."),
            (36, 386, "3. Follow attendance", "The roster refreshes while class is active. Faculty can open a student's profile and review classes attended."),
            (36, 480, "4. Close the session", "Ending the session prevents further check-ins. Recorded attendance remains available in history.")]
    right = [(316, 198, "1. Identify the account", "Student signs in with Google and links the account to an Enrollment ID unique within the institution."),
             (316, 292, "2. Open check-in", "Scan the classroom QR with the phone camera or follow its check-in link. Sign-in returns to that class."),
             (316, 386, "3. Confirm attendance", "The API verifies student access, active session, and current six-digit code before saving attendance."),
             (316, 480, "4. Recover or finish", "Expired code? Scan again or enter the new code. Duplicate check-ins are acknowledged without adding another record.")]
    for x, y, title, body in left:
        p.card(x, y, 256, 78, title, body, WHITE)
    for x, y, title, body in right:
        p.card(x, y, 256, 78, title, body, WHITE)
    p.text(36, 592, "ACCOUNT AND DEVICE", 8, GREEN, True)
    p.wrapped(36, 612, "Google identifies the account. The first sign-in binds it to a browser-generated device ID; a device reset revokes its active API sessions. Sign-in tokens currently last 12 hours.", 530, 9, MUTED, 13)
    p.rect(36, 676, 540, 50, GOLD, radius=8)
    p.text(49, 687, "PRODUCT LIMIT", 8, "8A6B29", True)
    p.wrapped(49, 702, "A rotating QR and device binding deter casual proxying; they cannot prove physical presence or stop a determined live relay.", 510, 8.3, INK, 11)
    return p


def institutions():
    p = base_page("A platform for many institutions", "Proposed administration model", 4)
    p.wrapped(36, 111, "The multi-institution layer is the proposed next phase. It adds scoped administration around the existing attendance workflow.", 530, 10, MUTED, 14)
    p.card(36, 151, 256, 164, "Global superadmin", "You are the platform owner. Create and suspend institutions, assign institution admins, see global health and activity, and review the global audit trail.", GOLD, "PLATFORM-WIDE")
    p.card(320, 151, 256, 164, "Institution admin", "Manage faculty and students only in the selected institution. Reset student devices, review attendance, and set local enrollment and QR policies.", BLUE, "TENANT-SCOPED")
    p.text(36, 345, "DATA AND ACCESS RULES", 8, GREEN, True)
    rules = [
        ("Membership-scoped roles", "A person's role is attached to their institution membership, not globally to their Google account."),
        ("Institution-local IDs", "Enrollment IDs are unique within an institution; the same ID can exist at another institution."),
        ("Tenant-isolated records", "Sessions, attendance, device controls, and reports are always filtered by institution."),
        ("Traceable admin actions", "Role changes, device resets, exports, and settings changes write actor, time, target, and institution to an audit log."),
        ("Safe removal", "Removing faculty access revokes sign-in and access but preserves historical class and attendance records."),
    ]
    y = 369
    for title, body in rules:
        p.rect(36, y, 540, 51, WHITE, BORDER, 7)
        p.text(49, y + 9, title, 9.5, INK, True)
        p.wrapped(205, y + 9, body, 350, 8.3, MUTED, 11)
        y += 59
    p.rect(36, 675, 540, 52, MINT, radius=8)
    p.text(49, 686, "CURRENT CODE VS. PROPOSED", 8, GREEN, True)
    p.wrapped(49, 700, "Google student/faculty sign-in, sessions, QR check-in, attendance, student profiles, and device reset exist in the codebase. Global superadmin, institution setup, and tenant-scoped institution admin are not implemented yet.", 510, 8, INK, 10.5)
    return p


def platform():
    p = base_page("Product foundation and next steps", "Pitch summary", 5)
    p.text(36, 112, "CURRENT APPLICATION", 8, GREEN, True)
    p.card(36, 132, 166, 106, "Web client", "React + Vite frontend hosted on Cloudflare. Works in a modern mobile or desktop browser.", WHITE)
    p.card(222, 132, 166, 106, "Attendance API", "FastAPI on Render verifies Google tokens, enforces roles, generates codes, and records attendance.", WHITE)
    p.card(408, 132, 168, 106, "Data store", "Supabase PostgreSQL stores accounts, device registrations, class sessions, and attendance.", WHITE)
    p.arrow([(202, 185), (222, 185)], GREEN)
    p.arrow([(388, 185), (408, 185)], GREEN)
    p.text(36, 278, "DELIVERY ROADMAP", 8, GREEN, True)
    rows = [
        ("01", "Institution foundation", "Add institutions, memberships, institution-scoped roles, and tenant-safe data access.", MINT),
        ("02", "Admin operations", "Build global institution setup, institution faculty/student controls, device reset, and audit log.", BLUE),
        ("03", "Operational reporting", "Add institution-level attendance exports, activity summaries, and configurable retention policies.", GOLD),
    ]
    y = 302
    for n, title, body, tint in rows:
        p.rect(36, y, 540, 82, tint, BORDER, 8)
        p.text(50, y + 15, n, 15, GREEN, True)
        p.text(91, y + 13, title, 11.5, INK, True)
        p.wrapped(91, y + 34, body, 465, 8.8, MUTED, 12)
        y += 94
    p.text(36, 603, "THE PITCH", 8, GREEN, True)
    p.rect(36, 622, 540, 92, NAVY, radius=10)
    p.wrapped(56, 641, "SmartRoll turns attendance into a quick, visible classroom workflow. Faculty controls the session; students confirm with a rotating QR; institution-level administration can scale the model while keeping each school's records separate.", 500, 13, WHITE, 19, True)
    return p


def build_pdf(pages):
    objs = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{5 + i*2} 0 R" for i in range(len(pages)))
    objs.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode())
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    for i, page in enumerate(pages):
        page_obj = 5 + i * 2
        content_obj = page_obj + 1
        stream = "\n".join(page.ops).encode("latin-1", "replace")
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page.width} {page.height}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_obj} 0 R >>".encode())
        objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objs, 1):
        offsets.append(len(data))
        data.extend(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    OUT.write_bytes(data)


if __name__ == "__main__":
    build_pdf([cover(), flowchart(), workflows(), institutions(), platform()])
    print(f"Created {OUT}")
