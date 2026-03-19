from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from core.settings import settings
from database.dependencies import get_db
from services.oauth_service import find_or_create_oauth_user
from utils.oauth_config import oauth
from utils.token import create_access_token, create_refresh_token
from repository.user_repository import save_refresh_token

router = APIRouter(prefix="/auth", tags=["oauth"])


@router.get("/google/login")
async def google_login(request: Request):
    """Redirect the user to Google's OAuth consent screen."""
    _store_frontend_redirect(request)
    redirect_uri = str(request.url_for("google_callback"))
    print("REDIRECT URI:", redirect_uri)
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, response: Response, db: Session = Depends(get_db)):
    """Google redirects here after the user logs in."""
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=400, detail="Google OAuth failed")

    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Could not fetch user info from Google")

    email = user_info.get("email")
    provider_id = user_info.get("sub")  # Google's unique user ID

    if not email or not provider_id:
        raise HTTPException(status_code=400, detail="Incomplete user info from Google")

    user = find_or_create_oauth_user(db, email=email, provider="google", provider_id=provider_id)

    return _issue_tokens_and_redirect(db, user, request)



@router.get("/github/login")
async def github_login(request: Request):
    """Redirect the user to GitHub's OAuth consent screen."""
    _store_frontend_redirect(request)
    redirect_uri = str(request.url_for("github_callback"))
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback", name="github_callback")
async def github_callback(request: Request, response: Response, db: Session = Depends(get_db)):
    """GitHub redirects here after the user logs in."""
    try:
        token = await oauth.github.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=400, detail="GitHub OAuth failed")

    # GitHub doesn't return user info in the token — need a separate API call
    resp = await oauth.github.get("user", token=token)
    github_user = resp.json()

    provider_id = str(github_user.get("id"))
    email = github_user.get("email")

    # GitHub users can have their email set to private — fetch it explicitly
    if not email:
        email = await _get_github_primary_email(token)

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Could not get email from GitHub. Make sure your GitHub email is not private, or grant email access."
        )

    user = find_or_create_oauth_user(db, email=email, provider="github", provider_id=provider_id)

    return _issue_tokens_and_redirect(db, user, request)


async def _get_github_primary_email(token: dict) -> str | None:
    """Fetch the primary verified email from GitHub's /user/emails endpoint."""
    resp = await oauth.github.get("user/emails", token=token)
    emails = resp.json()
    for entry in emails:
        if entry.get("primary") and entry.get("verified"):
            return entry.get("email")
    return None


def _issue_tokens_and_redirect(db, user, request: Request) -> RedirectResponse:
    """Create tokens, set the refresh token cookie, redirect to frontend."""
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    save_refresh_token(db, user.id, refresh_token)

    frontend_url = request.session.pop("oauth_redirect_to", None) or settings.frontend_url
    normalized_frontend_url = _normalize_frontend_url(frontend_url)

    if not normalized_frontend_url:
        raise HTTPException(status_code=500, detail="Invalid FRONTEND_URL for OAuth redirect")

    redirect = RedirectResponse(url=_append_query_param(normalized_frontend_url, "access_token", access_token))

    redirect.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=7 * 24 * 60 * 60
    )

    return redirect

@router.get("/auth/success")
def auth_success(request: Request):
    return {
        "message": "OAuth login successful",
        "access_token": request.query_params.get("access_token")
    }


def _store_frontend_redirect(request: Request) -> None:
    redirect_to = request.query_params.get("redirect_to") or request.headers.get("referer") or settings.frontend_url
    normalized_frontend_url = _normalize_frontend_url(redirect_to)
    if normalized_frontend_url:
        request.session["oauth_redirect_to"] = normalized_frontend_url


def _normalize_frontend_url(url: str | None) -> str | None:
    if not url:
        return None

    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return None

    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def _append_query_param(url: str, key: str, value: str) -> str:
    parts = urlsplit(url)
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    params[key] = value
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params), parts.fragment))
