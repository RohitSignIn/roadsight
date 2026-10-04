import type { VehicleRecord } from "../types/api";

export type LiveResult = {
  sequence: number; latency_ms: number; inference_fps: number;
  width?: number; height?: number;
  detections: Array<{class_name: string; confidence: number; box: {x1:number;y1:number;x2:number;y2:number}}>;
  vehicles: VehicleRecord[]; total_unique: number;
};
export interface LiveConnection { sendFrame(sequence:number,jpeg:string): boolean | void; close():void }
export function createLiveSocket(onResult:(r:LiveResult)=>void,onError:(m:string)=>void):LiveConnection {
  const socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/live`);
  let inFlight = false, latest = -1, closed = false;
  let timeout: ReturnType<typeof setTimeout> | undefined;
  socket.onmessage = event => {
    clearTimeout(timeout);
    inFlight = false;
    try {
      const body = JSON.parse(event.data);
      if (body.error) onError(body.error.message);
      else if (body.sequence > latest) { latest = body.sequence; onResult(body); }
    } catch { onError("Invalid response from the detection server."); }
  };
  socket.onclose = () => { clearTimeout(timeout); if (!closed) onError("Detection connection closed. Stop and restart the camera."); };
  socket.onerror = () => onError("Cannot connect to detection server. Check that the backend is running.");
  return {
    sendFrame(sequence,jpeg) {
      if (inFlight || socket.readyState !== WebSocket.OPEN || socket.bufferedAmount) return false;
      inFlight = true;
      socket.send(JSON.stringify({sequence,image:jpeg,confidence:0.25}));
      timeout = setTimeout(() => { onError("Detection timed out. Stop and restart the camera."); socket.close(); }, 30000);
      return true;
    },
    close() { closed = true; clearTimeout(timeout); socket.close(); },
  };
}
