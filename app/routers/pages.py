from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import require_admin

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/admin", response_class=HTMLResponse)
def admin(request: Request, _user: str = Depends(require_admin)):
    return templates.TemplateResponse("admin.html", {"request": request})
