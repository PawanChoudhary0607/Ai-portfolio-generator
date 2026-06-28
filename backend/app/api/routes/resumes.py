"""Resume upload + processing-status routes (Upload page, Steps 1–2)."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.models import Resume, User
from app.database.session import get_db
from app.schemas.resume import ResumeOut, ResumeProcessingStatus
from app.services import resume_service, storage_service

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeOut:
    content = await file.read()

    try:
        storage_service.validate_upload(file, content=content)
    except storage_service.UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)) from exc
    except storage_service.FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)
        ) from exc

    storage_path = storage_service.save_resume_pdf(content, user_id=current_user.id)

    resume = resume_service.create_resume_record(
        db,
        user_id=current_user.id,
        original_filename=file.filename or "resume.pdf",
        storage_path=storage_path,
        file_size_bytes=len(content),
    )

    # Pipeline runs after the response is sent — see resume_service.run_pipeline
    # for the production caveat about replacing this with a real task queue.
    background_tasks.add_task(resume_service.run_pipeline, resume.id)

    return ResumeOut.model_validate(resume)


@router.get("", response_model=list[ResumeOut])
def list_resumes(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ResumeOut]:
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .all()
    )
    return [ResumeOut.model_validate(r) for r in resumes]


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
    resume_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ResumeOut:
    resume = _get_owned_resume_or_404(db, resume_id, current_user.id)
    return ResumeOut.model_validate(resume)


@router.get("/{resume_id}/status", response_model=ResumeProcessingStatus)
def get_resume_status(
    resume_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ResumeProcessingStatus:
    resume = _get_owned_resume_or_404(db, resume_id, current_user.id)
    payload = resume_service.get_processing_status(db, resume)
    return ResumeProcessingStatus.model_validate(payload)


def _get_owned_resume_or_404(db: Session, resume_id: str, user_id: str) -> Resume:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume
