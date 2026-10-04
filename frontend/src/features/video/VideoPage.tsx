import { useEffect,useRef,useState } from "react";
import { apiClient } from "../../api/http";
import { VehicleTable } from "../../components/VehicleTable";
import type { VideoJob } from "../../types/api";
const MAX=10*1024*1024;
type Props={submitVideo?:(f:File)=>Promise<VideoJob>;getJob?:(id:string)=>Promise<VideoJob>;cancelJob?:(id:string)=>Promise<VideoJob>;pollInterval?:number};
export function VideoPage({submitVideo=apiClient.submitVideo,getJob=apiClient.getJob,cancelJob=apiClient.cancelJob,pollInterval=600}:Props){
  const [file,setFile]=useState<File|null>(null),[job,setJob]=useState<VideoJob|null>(null),[error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const generation=useRef(0),locked=useRef(false);
  useEffect(()=>()=>{generation.current++;},[]);
  function choose(next:File|null){
    generation.current++; locked.current=false; setBusy(false); setJob(null);
    if(next&&next.size>MAX){setFile(null);setError("Video must be 10 MB or smaller.");}
    else{setFile(next);setError("");}
  }
  async function process(){
    if(!file||locked.current)return;
    locked.current=true;setBusy(true);setError("");const token=++generation.current;
    try{
      let current=await submitVideo(file);
      while(token===generation.current){
        setJob(current);
        if(current.status!=="queued"&&current.status!=="processing"){
          if(current.status==="failed")setError(current.error??"Processing failed.");
          if(current.status==="expired")setError("Results expired. Please process the video again.");
          break;
        }
        await new Promise(r=>setTimeout(r,pollInterval));
        if(token!==generation.current)break;
        current=await getJob(current.id);
      }
    }catch(e){if(token===generation.current)setError(e instanceof Error?e.message:"Processing failed.");}
    finally{if(token===generation.current){locked.current=false;setBusy(false);}}
  }
  async function cancel(){
    if(!job)return;
    try{const cancelled=await cancelJob(job.id);generation.current++;setJob(cancelled);locked.current=false;setBusy(false);}
    catch(e){setError(e instanceof Error?e.message:"Could not cancel the job.");}
  }
  return <section className="page"><header className="page-title"><span className="eyebrow">TEMPORAL TRACKING</span><h1>Video detection</h1><p>Process up to 10 MB of video with unique vehicle history.</p></header>
    <div className="workspace"><div className="panel upload-panel"><label className="file-label">Choose video<input aria-label="Choose video" type="file" accept=".mp4,.webm,.avi,.mov" disabled={busy} onChange={e=>choose(e.target.files?.[0]??null)}/></label>
    {file&&<p>{file.name} · {(file.size/1024/1024).toFixed(2)} MB</p>}
    <button className="primary" disabled={!file||busy} onClick={process}>{busy?"Processing…":"Process video"}</button>
    {error&&<p role="alert" className="error-text">{error}</p>}</div>
    <div className="panel result-panel">{job?<><div className="job-status"><span>{job.status}</span><strong>{Math.round(job.progress*100)}%</strong></div><progress max={1} value={job.progress}/>
    {busy&&<button className="button secondary" onClick={cancel}>Cancel</button>}
    {job.download_ready&&<>{job.preview_url&&<video controls className="result-image" src={job.preview_url} aria-label="Processed video"/>}<VehicleTable vehicles={job.vehicles??[]}/><a className="button primary" href={apiClient.downloadUrl(job.id)}>Download results</a></>}
    </>:<p className="placeholder">Processing progress and results will appear here.</p>}</div></div>
  </section>;
}
