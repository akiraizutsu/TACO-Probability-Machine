"""Basic Auth for admin endpoints."""
import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASS", "")
    if not admin_pass:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_PASS is not configured on the server",
        )
    user_ok = secrets.compare_digest(credentials.username.encode(), admin_user.encode())
    pass_ok = secrets.compare_digest(credentials.password.encode(), admin_pass.encode())
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
