from pydantic import BaseModel, Field


class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    box: Box


class HealthResponse(BaseModel):
    ready: bool
    device: str | None = None
    model: str | None = None
    message: str | None = None


class VehicleRecord(BaseModel):
    vehicle_id: int
    vehicle_type: str
    color: str = "unknown"
    first_seen: float
    last_seen: float
    duration_seconds: float
    direction: str = "stationary"
    average_confidence: float = Field(ge=0.0, le=1.0)
    maximum_confidence: float = Field(ge=0.0, le=1.0)
    relative_size: float = Field(ge=0.0)


class TrackedDetection(BaseModel):
    track_id: int
    detection: Detection
    color: str = "unknown"
    direction: str = "stationary"
    relative_size: float = Field(ge=0.0)


class ImageDetectionResponse(BaseModel):
    download_url: str | None = None
    annotated_image_base64: str
    vehicles: list[VehicleRecord]
