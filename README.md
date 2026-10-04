# RoadSight — Local Vehicle Detection

RoadSight is a local-first vehicle detection web application built around the trained YOLO checkpoint in `models/best.pt`. It supports images, uploaded videos, and a live webcam, with unique-vehicle tracking, broad color estimation, screen-relative direction, and downloadable history reports.

## Features

- Detect and classify vehicles with the existing custom YOLO model.
- Upload an image and download its annotated result.
- Process videos up to 10 MB as cancellable background jobs.
- Count each tracked vehicle once instead of once per frame.
- Estimate broad vehicle color and on-screen movement direction.
- Download processed video, CSV, JSON, summaries, and ZIP bundles.
- Run live webcam detection with a smooth Canvas overlay.
- Record the annotated webcam Canvas to WebM entirely in the browser.
- Download webcam history as CSV or JSON without uploading the recording.
- Use NVIDIA CUDA automatically when supported; otherwise run on CPU.

## Requirements

- Windows PowerShell
- Python 3.11
- Node.js and npm; Microsoft Edge for the optional browser test suite
- FFmpeg is supplied by the Python `imageio-ffmpeg` dependency (no separate PATH installation required)
- The trained checkpoint at `models/best.pt`

## First-time setup

The trained vehicle detection checkpoint is included in this repository at `models/best.pt` and is ready to use after cloning.

From the repository root:

```powershell
uv python install 3.11
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -e ".\backend[test]"
npm --prefix frontend install
```

## Start the application

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

Open <http://127.0.0.1:5173>. API documentation is available at <http://127.0.0.1:8010/docs>.

To run the services separately:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8010
npm --prefix frontend run dev
```

## Verify the project

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

This runs the backend suite (excluding the opt-in real-checkpoint test), frontend tests, TypeScript validation, and the production build.

To also run the browser tests with the real checkpoint and a synthetic webcam:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -E2E
```

Browser tests use ports 8011 and 5189 and require those ports to be free. They do not access your physical webcam. Temporary test media and reports are ignored by Git.

## Webcam support

The application uses the browser's default camera: built-in laptop cameras, USB webcams, and virtual cameras exposed by the operating system. There is no camera-selector or direct RTSP/IP-camera input yet.

- Edge has been tested end to end using a synthetic camera and the real checkpoint, including WebM recording.
- Chrome uses the same browser APIs but has not been verified in this project. Firefox/Safari and mobile devices have not been tested; recording depends on WebM support detected at runtime.
- Open the site on localhost/127.0.0.1 and allow camera permission. Remote access requires HTTPS; ordinary LAN HTTP is not supported for camera capture.
- Stop other applications using the webcam if the browser reports that it is busy.
- Frames are resized to a maximum width of 640 pixels for inference. Only one browser request is in flight; the backend retains only the newest pending frame. Display drawing is independent of inference speed.
- Recording is silent WebM, stored in browser memory until saved. Long recordings can consume substantial memory. No physical-camera FPS guarantee has been measured.
- Stopping the camera or navigating away stops camera and recording tracks. Save the recording before leaving the page.

Browser API references: [camera permissions and secure contexts](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia), [recording format detection](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static).

## Privacy and temporary files

Uploaded videos and generated bundles are stored under `.runtime/jobs` using random job IDs. Uploads are removed after processing. Results expire one hour after completion and cleanup runs every 60 seconds and on startup. Active processing and file transfers hold leases to prevent deletion. Failed/cancelled jobs remove incomplete outputs. Original filenames are never used as filesystem paths. Webcam recordings remain in browser memory and are downloaded directly to the client; they are not stored by FastAPI.

Images offer JPEG, CSV, JSON and ZIP downloads. Completed videos offer an in-page H.264 preview, filterable timestamped history, class counts and a ZIP containing MP4, CSV/JSON, summary and representative crops. Processed videos preserve source FPS but omit audio. Background camera motion is estimated; insufficient motion evidence results in uncertain direction.

## Accuracy and performance notes

- Color is a broad visual estimate and may be unreliable with poor lighting, reflections, or tiny crops.
- Direction is measured in screen coordinates and is intended for fixed or mostly stationary cameras.
- ByteTrack preserves identities through short gaps but does not guarantee re-identification after a vehicle leaves and later returns.
- CPU inference speed depends on the processor, video resolution, and number of vehicles. The webcam display remains smooth while inference runs at a lower cadence.
- MP4, WebM, AVI, and MOV uploads are accepted only when OpenCV can decode their actual contents.
