import hashlib
import os
import secrets
import time
from datetime import datetime, timedelta
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import pyotp
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DBSession

load_dotenv()

from database import Base, engine, get_db
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartRoll Attendance API", version="2.0.0")
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

TOKEN_TTL_HOURS = 12
TOTP_INTERVAL = 30


class GoogleSignInRequest(BaseModel):
    credential: str
    device_id: str = Field(min_length=20, max_length=80)


class AttendanceRequest(BaseModel):
    session_id: int
    totp_code: str = Field(min_length=6, max_length=6)


class StartSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


def faculty_emails():
    return {value.strip().lower() for value in os.getenv("FACULTY_EMAILS", "").split(",") if value.strip()}


def verify_google_credential(credential: str):
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    try:
        claims = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified.")
    if not claims.get("email_verified"):
        raise HTTPException(status_code=401, detail="Use a verified Google account.")
    if not claims.get("sub") or not claims.get("email"):
        raise HTTPException(status_code=401, detail="Google did not provide a verified account.")
    return claims


def identity_payload(user, identity):
    return {
        "id": user.id,
        "name": user.name,
        "email": identity.email,
        "role": "faculty" if user.role == "TEACHER" else "student",
        "device_registered": bool(identity.device_id),
    }


def get_auth_context(authorization: str | None, db: DBSession):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = db.query(models.AuthSession).filter(models.AuthSession.token_hash == token_hash).first()
    if not session or session.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=401, detail="Your sign-in has expired. Sign in again.")
    user = db.query(models.User).filter(models.User.id == session.user_id).first()
    identity = db.query(models.GoogleIdentity).filter(models.GoogleIdentity.user_id == session.user_id).first()
    if not user or not identity or not identity.device_id or identity.device_id != session.device_id:
        raise HTTPException(status_code=401, detail="This device is no longer registered. Sign in again.")
    return user, identity, token_hash


def require_user(authorization: str | None = Header(default=None), db: DBSession = Depends(get_db)):
    return get_auth_context(authorization, db)


def require_faculty(auth=Depends(require_user)):
    user, identity, token_hash = auth
    if user.role != "TEACHER" or identity.email.lower() not in faculty_emails():
        raise HTTPException(status_code=403, detail="Faculty access is not enabled for this account.")
    return auth


def require_student(auth=Depends(require_user)):
    user, identity, token_hash = auth
    if user.role != "STUDENT":
        raise HTTPException(status_code=403, detail="This check-in is for student accounts.")
    return auth


def attendance_record(db, attendance):
    student = attendance.student
    identity = student_identity_for_user(db, student.id)
    return {
        "id": attendance.id,
        "student_id": student.id,
        "student_name": student.name,
        "roll_number": identity.email if identity else student.roll_number,
        "google_identity_id": identity.id if identity else None,
        "timestamp": attendance.timestamp.isoformat() + "Z" if attendance.timestamp else None,
    }


def student_identity_for_user(db, user_id):
    return db.query(models.GoogleIdentity).filter(models.GoogleIdentity.user_id == user_id).first()


def session_payload(db, session, include_code=True):
    _, code, remaining = get_current_totp(session.totp_secret)
    attendances = db.query(models.Attendance).filter(
        models.Attendance.session_id == session.id
    ).order_by(models.Attendance.timestamp.desc()).all()
    result = {
        "session_id": session.id,
        "title": session.title,
        "is_active": session.is_active,
        "time_remaining": remaining,
        "interval": TOTP_INTERVAL,
        "total_students_present": len(attendances),
        "students": [attendance_record(db, item) for item in attendances],
    }
    if include_code:
        result["totp_code"] = code
    return result


def get_current_totp(secret: str):
    totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL)
    now = int(time.time())
    return totp, totp.now(), TOTP_INTERVAL - (now % TOTP_INTERVAL)


@app.get("/")
@app.get("/status")
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "SmartRoll Attendance API"}


@app.post("/api/auth/google")
def google_sign_in(req: GoogleSignInRequest, db: DBSession = Depends(get_db)):
    claims = verify_google_credential(req.credential)
    sub = claims["sub"]
    email = claims["email"].strip().lower()
    is_faculty = email in faculty_emails()

    identity = db.query(models.GoogleIdentity).filter(models.GoogleIdentity.google_sub == sub).first()
    if identity:
        user = db.query(models.User).filter(models.User.id == identity.user_id).first()
        if not user:
            raise HTTPException(status_code=409, detail="Account needs administrator repair.")
        if identity.device_id and identity.device_id != req.device_id:
            raise HTTPException(status_code=409, detail="This Google account is already registered on another device. Ask faculty to reset the device before moving.")
        if identity.device_id is None:
            used = db.query(models.GoogleIdentity).filter(models.GoogleIdentity.device_id == req.device_id).first()
            if used:
                raise HTTPException(status_code=409, detail="This device is already registered to another account.")
            identity.device_id = req.device_id
        identity.email = email
        user.name = claims.get("name") or user.name
        user.role = "TEACHER" if is_faculty else "STUDENT"
    else:
        used = db.query(models.GoogleIdentity).filter(models.GoogleIdentity.device_id == req.device_id).first()
        if used:
            raise HTTPException(status_code=409, detail="This device is already registered to another account.")
        user = models.User(
            name=claims.get("name") or email.split("@")[0],
            roll_number=f"GOOGLE-{sub}",
            role="TEACHER" if is_faculty else "STUDENT",
        )
        db.add(user)
        db.flush()
        identity = models.GoogleIdentity(
            google_sub=sub,
            email=email,
            user_id=user.id,
            device_id=req.device_id,
        )
        db.add(identity)
    db.flush()

    raw_token = secrets.token_urlsafe(48)
    db.add(models.AuthSession(
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        user_id=user.id,
        device_id=req.device_id,
        expires_at=datetime.utcnow() + timedelta(hours=TOKEN_TTL_HOURS),
    ))
    db.commit()
    return {
        "access_token": raw_token,
        "token_type": "bearer",
        "expires_in": TOKEN_TTL_HOURS * 3600,
        "user": identity_payload(user, identity),
    }


@app.get("/api/auth/me")
def auth_me(auth=Depends(require_user)):
    user, identity, _ = auth
    return {"user": identity_payload(user, identity)}


@app.post("/api/auth/logout")
def auth_logout(auth=Depends(require_user), db: DBSession = Depends(get_db)):
    _, _, token_hash = auth
    db.query(models.AuthSession).filter(models.AuthSession.token_hash == token_hash).delete()
    db.commit()
    return {"success": True}


@app.post("/api/faculty/sessions")
def start_faculty_session(req: StartSessionRequest, auth=Depends(require_faculty), db: DBSession = Depends(get_db)):
    user, _, _ = auth
    for old in db.query(models.Session).filter(models.Session.is_active.is_(True), models.Session.teacher_id == user.id).all():
        old.is_active = False
    session = models.Session(title=req.title.strip(), totp_secret=pyotp.random_base32(), is_active=True, teacher_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "title": session.title, "is_active": session.is_active}


@app.get("/api/faculty/sessions/active")
def get_faculty_active_session(auth=Depends(require_faculty), db: DBSession = Depends(get_db)):
    user, _, _ = auth
    session = db.query(models.Session).filter(models.Session.is_active.is_(True), models.Session.teacher_id == user.id).order_by(models.Session.id.desc()).first()
    if not session:
        return {"session": None}
    return {"session": session_payload(db, session)}


@app.get("/api/faculty/sessions/{session_id}")
def get_faculty_session(session_id: int, auth=Depends(require_faculty), db: DBSession = Depends(get_db)):
    user, _, _ = auth
    session = db.query(models.Session).filter(models.Session.id == session_id, models.Session.teacher_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"session": session_payload(db, session)}


@app.get("/api/faculty/sessions/{session_id}/display")
def get_classroom_display(session_id: int, auth=Depends(require_faculty), db: DBSession = Depends(get_db)):
    user, _, _ = auth
    session = db.query(models.Session).filter(models.Session.id == session_id, models.Session.teacher_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Class session not found.")
    _, code, remaining = get_current_totp(session.totp_secret)
    return {"session_id": session.id, "title": session.title, "is_active": session.is_active,
            "totp_code": code, "time_remaining": remaining, "interval": TOTP_INTERVAL}


@app.post("/api/faculty/sessions/{session_id}/end")
def end_faculty_session(session_id: int, auth=Depends(require_faculty), db: DBSession = Depends(get_db)):
    user, _, _ = auth
    session = db.query(models.Session).filter(models.Session.id == session_id, models.Session.teacher_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Class session not found.")
    session.is_active = False
    db.commit()
    return {"success": True}


@app.get("/api/student/sessions/{session_id}")
def get_student_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Class session not found.")
    return {"session_id": session.id, "title": session.title, "is_active": session.is_active}


@app.post("/api/student/attendance")
async def mark_student_attendance(req: AttendanceRequest, auth=Depends(require_student), db: DBSession = Depends(get_db)):
    user, identity, _ = auth
    session = db.query(models.Session).filter(models.Session.id == req.session_id).first()
    if not session or not session.is_active:
        raise HTTPException(status_code=410, detail="This class session has ended.")
    totp, _, _ = get_current_totp(session.totp_secret)
    if not totp.verify(req.totp_code, valid_window=0):
        raise HTTPException(status_code=400, detail="This check-in code has expired. Scan the current classroom code.")
    existing = db.query(models.Attendance).filter(
        models.Attendance.session_id == session.id,
        models.Attendance.student_id == user.id,
    ).first()
    if existing:
        return {"success": True, "already_marked": True, "message": "Your attendance is already recorded.", "attendance": attendance_record(db, existing)}
    record = models.Attendance(student_id=user.id, session_id=session.id)
    db.add(record)
    db.commit()
    db.refresh(record)
    response = attendance_record(db, record)
    response["message"] = "Attendance recorded."
    return {"success": True, "already_marked": False, "message": "Attendance recorded.", "attendance": response}


@app.post("/api/faculty/students/{identity_id}/reset-device")
def reset_student_device(identity_id: int, auth=Depends(require_faculty), db: DBSession = Depends(get_db)):
    identity = db.query(models.GoogleIdentity).filter(models.GoogleIdentity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Student account not found.")
    identity.device_id = None
    db.query(models.AuthSession).filter(models.AuthSession.user_id == identity.user_id).delete()
    db.commit()
    return {"success": True, "message": "Device registration reset. Student can sign in on their new device."}


@app.get("/api/faculty/students")
def list_student_accounts(auth=Depends(require_faculty), db: DBSession = Depends(get_db)):
    identities = db.query(models.GoogleIdentity).join(models.User).filter(models.User.role == "STUDENT").order_by(models.User.name.asc()).all()
    return {"students": [{
        "identity_id": identity.id,
        "name": identity.user.name,
        "email": identity.email,
        "device_registered": bool(identity.device_id),
    } for identity in identities]}
