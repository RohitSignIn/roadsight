import { useCallback,useEffect,useRef,useState } from "react";
import { Camera,CameraOff,Circle,Download,Square } from "lucide-react";
import { createLiveSocket,type LiveConnection,type LiveResult } from "../../api/liveSocket";
import { DetectionCanvas } from "./DetectionCanvas";
import { VehicleTable } from "../../components/VehicleTable";
import { useCanvasRecorder } from "./useCanvasRecorder";
import { buildSessionCsv,buildSessionJson,downloadText } from "./sessionReport";
type Props={socketFactory?:(onResult:(r:LiveResult)=>void,onError:(m:string)=>void)=>LiveConnection};

export function LivePage({socketFactory=createLiveSocket}:Props) {
  const videoRef=useRef<HTMLVideoElement>(null);
  const [canvas,setCanvas]=useState<HTMLCanvasElement|null>(null);
  const stream=useRef<MediaStream|null>(null), socket=useRef<LiveConnection|null>(null);
  const timer=useRef<ReturnType<typeof setTimeout>|null>(null);
  const generation=useRef(0), starting=useRef(false);
  const [active,setActive]=useState(false), [busy,setBusy]=useState(false);
  const [result,setResult]=useState<LiveResult|null>(null), [error,setError]=useState("");
  const recorder=useCanvasRecorder(canvas);
  const release=useCallback(()=>{
    generation.current++; starting.current=false;
    if(timer.current!==null) clearTimeout(timer.current);
    stream.current?.getTracks().forEach(t=>t.stop());
    socket.current?.close(); stream.current=null; socket.current=null;
  },[]);
  useEffect(()=>release,[release]);
  function stop(){recorder.stop(); release(); setActive(false); setBusy(false);}
  async function start(){
    if(starting.current||stream.current) return;
    const token=++generation.current; starting.current=true; setBusy(true); setError(""); setResult(null);
    try {
      if(!navigator.mediaDevices?.getUserMedia) throw new Error("Camera access requires localhost or HTTPS and a supported browser.");
      const media=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:1280},height:{ideal:720}},audio:false});
      if(token!==generation.current){media.getTracks().forEach(t=>t.stop());return;}
      stream.current=media;
      if(videoRef.current){videoRef.current.srcObject=media; await Promise.resolve(videoRef.current.play());}
      if(token!==generation.current) return;
      let sequence=0, interval=100, lastSent=0;
      socket.current=socketFactory(value=>{
        if(token!==generation.current) return;
        interval=Math.max(67,Math.min(1000,value.latency_ms*1.1));
        setResult(value);
      },message=>{if(token===generation.current)setError(message);});
      const capture=document.createElement("canvas");
      const tick=()=>{
        if(token!==generation.current)return;
        const v=videoRef.current;
        if(v?.videoWidth && performance.now()-lastSent>=interval){
          const scale=Math.min(1,640/v.videoWidth);
          capture.width=Math.round(v.videoWidth*scale); capture.height=Math.round(v.videoHeight*scale);
          capture.getContext("2d")?.drawImage(v,0,0,capture.width,capture.height);
          socket.current?.sendFrame(++sequence,capture.toDataURL("image/jpeg",.72).split(",")[1]);
          lastSent=performance.now();
        }
        timer.current=setTimeout(tick,33);
      };
      tick(); setActive(true);
    } catch(e) {
      if(token!==generation.current)return;
      release();
      const name=e instanceof Error?e.name:"";
      setError(name==="NotAllowedError"?"Camera permission was denied. Allow camera access in your browser.":name==="NotFoundError"?"No webcam was found. Connect a camera and try again.":name==="NotReadableError"?"The camera is busy or unavailable. Close other apps using it.":e instanceof Error?e.message:"Could not start the camera.");
    } finally {if(token===generation.current||!stream.current){starting.current=false;setBusy(false);}}
  }
  function report(type:"csv"|"json"){
    const records=result?.vehicles??[];
    downloadText(`vehicle-history.${type}`,type==="csv"?buildSessionCsv(records):buildSessionJson(records,{source:"webcam",created_at:new Date().toISOString()}),type==="csv"?"text/csv":"application/json");
  }
  return <section className="page">
    <header className="page-title"><span className="eyebrow">REAL-TIME DETECTION</span><h1>Live camera</h1><p>Camera frames are processed by your local backend. Recordings stay in this browser.</p></header>
    <div className="live-layout"><div className="live-stage"><video ref={videoRef} muted playsInline/>
      <DetectionCanvas ref={setCanvas} video={videoRef.current} result={result}/>
      {!active&&<div className="live-empty"><Camera size={45}/><p>Start the camera to begin vehicle detection.</p></div>}
    </div><aside className="panel live-sidebar">
      <div className="live-count"><strong>{result?.total_unique??0}</strong><span>Unique vehicles</span></div>
      <div className="live-actions">
        {active||busy?<button className="button secondary" onClick={stop}><CameraOff/>Stop camera</button>:<button className="button primary" onClick={start}><Camera/>Start camera</button>}
        {active&&!recorder.recording&&<button className="button secondary" onClick={recorder.start}><Circle/>Record</button>}
        {recorder.recording&&<button className="button secondary" onClick={recorder.stop}><Square/>Stop recording</button>}
        {recorder.video&&<button className="button primary" onClick={recorder.save}><Download/>Save WebM</button>}
      </div>
      {result&&<><p>{result.inference_fps} inference FPS · {result.latency_ms} ms</p><VehicleTable vehicles={result.vehicles}/><button className="button secondary" onClick={()=>report("csv")}>Download CSV</button><button className="button secondary" onClick={()=>report("json")}>Download JSON</button></>}
      {(error||recorder.error)&&<p role="alert" className="error-text">{error||recorder.error}</p>}
    </aside></div>
  </section>;
}
