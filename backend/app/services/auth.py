"""Minimal guest-identity resolution.

There's no signup/login yet — every visitor is resolved to a User row via a
long-lived `guest_id` cookie, created lazily on first visit. This keeps a
single ownership column (Workspace.user_id) that works the same whether the
owner is a guest or (later) a real signed-up user: a future signup flow just
fills in email/password_hash on the same User row.
"""
import uuid

from flask import g, request

from app.extensions import db
from app.models import User

GUEST_COOKIE_NAME = "guest_id"
GUEST_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year


def resolve_current_user():
    """Flask before_request hook: resolve the caller's User from their
    guest_id cookie, creating both a fresh guest_id and User row if this is
    their first visit (or their cookie doesn't match any existing user).
    Stashes the result on flask.g for route handlers to use."""
    incoming = request.cookies.get(GUEST_COOKIE_NAME)
    user = User.query.filter_by(guest_id=incoming).first() if incoming else None

    g.new_guest_id = None
    if user is None:
        new_guest_id = incoming or str(uuid.uuid4())
        user = User(is_guest=True, guest_id=new_guest_id)
        db.session.add(user)
        db.session.commit()
        g.new_guest_id = new_guest_id

    g.current_user = user


def set_guest_cookie(response):
    """Flask after_request hook: (re)issue the guest_id cookie whenever
    resolve_current_user had to mint a new one."""
    new_guest_id = getattr(g, "new_guest_id", None)
    if new_guest_id:
        response.set_cookie(
            GUEST_COOKIE_NAME,
            new_guest_id,
            httponly=True,
            samesite="Lax",
            secure=False,  # local HTTP dev only; needs True behind HTTPS
            max_age=GUEST_COOKIE_MAX_AGE,
        )
    return response
