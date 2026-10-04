import { useState } from "react";
import { apiClient } from "../../api/http";
import { VehicleTable } from "../../components/VehicleTable";
import { buildSessionCsv,buildSessionJson,downloadText } from "../live/sessionReport";
import type { ImageResult } from "../../types/api";
export function ImagePage({detectImage=apiClient.detectImage}:{detectImage?:(file:File)=>Promise<ImageResult>}){
  const [file,setFile]=useState<File|null>(null),[result,setResult]=useState<ImageResult|null>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
  async function submit(){if(!file||busy)return;setBusy(true);setError("");setResult(null);try{setResult(await detectImage(file));}catch(e){setError(e instanceof Error?e.message:"Detection failed.");}finally{setBusy(false);}}
  const imageUrl=result?`data:image/jpeg;base64,${result.annotated_image_base64}`:"";
  return <section className="page"><header className="page-title"><span className="eyebrow">STATIC ANALYSIS</span><h1>Image detection</h1><p>Upload an image up to 10 MB to detect vehicles and export results.</p></header>
    <div className="workspace"><div className="panel upload-panel"><label className="file-label">Choose image<input aria-label="Choose image" type="file" accept="image/*" disabled={busy} onChange={e=>{setFile(e.target.files?.[0]??null);setResult(null);}}/></label>
    {file&&<p>{file.name}</p>}<button className="primary" disabled={!file||busy} onClick={submit}>{busy?"Detecting…":"Detect vehicles"}</button>{error&&<p role="alert" className="error-text">{error}</p>}</div>
    <div className="panel result-panel">{result?<><img className="result-image" src={imageUrl} alt="Annotated detection result"/><div className="result-heading"><h2>Detection results</h2><a className="button secondary" href={imageUrl} download="detected-vehicles.jpg">Download image</a></div><VehicleTable vehicles={result.vehicles}/>
    <div><button className="button secondary" onClick={()=>downloadText("vehicle-history.csv",buildSessionCsv(result.vehicles),"text/csv")}>Download CSV</button><button className="button secondary" onClick={()=>downloadText("vehicle-history.json",buildSessionJson(result.vehicles,{source:"image"}),"application/json")}>Download JSON</button>{result.download_url&&<a className="button primary" href={result.download_url}>Download ZIP</a>}</div>
    </>:<p className="placeholder">Your annotated image will appear here.</p>}</div></div>
  </section>;
}
