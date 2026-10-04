import { forwardRef,useCallback,useEffect,useRef } from "react";
import type { LiveResult } from "../../api/liveSocket";
export const DetectionCanvas=forwardRef<HTMLCanvasElement,{video:HTMLVideoElement|null;result:LiveResult|null}>(({video,result},ref)=>{
  const local=useRef<HTMLCanvasElement|null>(null), latest=useRef(result);
  latest.current=result;
  const assign=useCallback((node:HTMLCanvasElement|null)=>{local.current=node;if(typeof ref==="function")ref(node);else if(ref)ref.current=node;},[ref]);
  useEffect(()=>{
    let id=0;
    const draw=()=>{
      const c=local.current;
      if(c&&video?.videoWidth){
        if(c.width!==video.videoWidth||c.height!==video.videoHeight){c.width=video.videoWidth;c.height=video.videoHeight;}
        const x=c.getContext("2d"); x?.drawImage(video,0,0,c.width,c.height);
        const value=latest.current;
        if(x&&value){
          const sx=c.width/(value.width??c.width),sy=c.height/(value.height??c.height);
          x.strokeStyle="#72e39a";x.fillStyle="#72e39a";x.lineWidth=3;x.font="600 15px sans-serif";
          value.detections.forEach(d=>{const b=d.box;x.strokeRect(b.x1*sx,b.y1*sy,(b.x2-b.x1)*sx,(b.y2-b.y1)*sy);x.fillText(`${d.class_name} ${Math.round(d.confidence*100)}%`,b.x1*sx,Math.max(16,b.y1*sy-6));});
        }
      }
      id=requestAnimationFrame(draw);
    };
    id=requestAnimationFrame(draw);return()=>cancelAnimationFrame(id);
  },[video]);
  return <canvas ref={assign} className="live-canvas"/>;
});
