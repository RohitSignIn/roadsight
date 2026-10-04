from fastapi import APIRouter, Request

from backend.app.schemas import HealthResponse


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    runtime = request.app.state.runtime
    settings = request.app.state.settings
    if runtime is None:
        return HealthResponse(
            ready=False,
            model=settings.model_path.name,
            message="Vehicle detection model is unavailable.",
        )
    return HealthResponse(ready=True, device=runtime.device, model=runtime.model_name)

