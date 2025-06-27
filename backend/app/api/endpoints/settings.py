from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def get_settings(db: Session = Depends(get_db)):
    """Get application settings"""
    return {
        "theme": "light",
        "auto_save": True,
        "show_coordinates": True
    }

@router.post("/")
async def update_settings(settings: dict, db: Session = Depends(get_db)):
    """Update application settings"""
    return {"message": "Settings updated successfully"}