import { useCallback, useEffect, useRef, useState } from "react";
const codecs = ["video/webm;codecs=vp9","video/webm;codecs=vp8","video/webm"];
export function selectSupportedMimeType(check?: (type:string)=>boolean) {
  if (!check && typeof MediaRecorder === "undefined") return null;
  return codecs.find(check ?? (type => MediaRecorder.isTypeSupported(type))) ?? null;
}
export function useCanvasRecorder(canvas:HTMLCanvasElement|null,fps=30) {
  const recorder = useRef<MediaRecorder|null>(null);
  const stream = useRef<MediaStream|null>(null);
  const mounted = useRef(true);
  const [recording,setRecording] = useState(false);
  const [video,setVideo] = useState<Blob|null>(null);
  const [error,setError] = useState("");
  const stop = useCallback(() => {
    if (recorder.current?.state === "recording") recorder.current.stop();
    stream.current?.getTracks().forEach(track => track.stop());
    stream.current = null;
    if (mounted.current) setRecording(false);
  },[]);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; stop(); }; },[stop]);
  function start() {
    setError("");
    const mime = selectSupportedMimeType();
    if (!canvas?.captureStream || !mime) { setError("WebM recording is unavailable in this browser. Try desktop Chrome or Edge."); return; }
    if (recorder.current?.state === "recording") return;
    try {
      stream.current = canvas.captureStream(fps);
      const next = new MediaRecorder(stream.current,{mimeType:mime});
      const chunks:Blob[] = [];
      next.ondataavailable = e => { if(e.data.size) chunks.push(e.data); };
      next.onstop = () => { if(mounted.current) setVideo(new Blob(chunks,{type:mime})); };
      next.onerror = () => { stop(); if(mounted.current) setError("Recording failed. Please try again."); };
      recorder.current = next;
      next.start(1000);
      setVideo(null); setRecording(true);
    } catch { stop(); setError("Could not start recording in this browser."); }
  }
  function save() {
    if(!video) return;
    const url = URL.createObjectURL(video);
    const a = document.createElement("a"); a.href=url; a.download="vehicle-detection-live.webm"; a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return {recording,video,error,start,stop,save};
}
