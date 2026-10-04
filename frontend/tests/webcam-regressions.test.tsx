import { act,render,renderHook,screen,waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach,vi } from "vitest";
import { useCanvasRecorder } from "../src/features/live/useCanvasRecorder";
import { LivePage } from "../src/features/live/LivePage";
import { createLiveSocket } from "../src/api/liveSocket";

afterEach(()=>{vi.unstubAllGlobals();vi.restoreAllMocks();});
test("unmount stops an active recorder and canvas tracks",()=>{
  const stopTrack=vi.fn();
  class Recorder {
    static isTypeSupported(){return true;}
    state="inactive";onstop?:()=>void;ondataavailable?:()=>void;
    start(){this.state="recording";}
    stop=vi.fn(()=>{this.state="inactive";this.onstop?.();});
  }
  vi.stubGlobal("MediaRecorder",Recorder);
  const canvas={captureStream:()=>({getTracks:()=>[{stop:stopTrack}]})} as unknown as HTMLCanvasElement;
  const {result,unmount}=renderHook(()=>useCanvasRecorder(canvas));
  act(()=>result.current.start());
  expect(result.current.recording).toBe(true);
  unmount();
  expect(stopTrack).toHaveBeenCalledOnce();
});
test("unsupported recording reports an error instead of throwing",()=>{
  vi.stubGlobal("MediaRecorder",undefined);
  const {result}=renderHook(()=>useCanvasRecorder({} as HTMLCanvasElement));
  act(()=>result.current.start());
  expect(result.current.error).toMatch(/unavailable/i);
});
test("camera permission resolving after navigation releases its stream",async()=>{
  let resolve!:(stream:MediaStream)=>void;
  const stop=vi.fn();
  Object.defineProperty(navigator,"mediaDevices",{configurable:true,value:{getUserMedia:()=>new Promise<MediaStream>(r=>{resolve=r;})}});
  const {unmount}=render(<LivePage/>);
  await userEvent.click(screen.getByRole("button",{name:/start camera/i}));
  unmount();
  await act(async()=>resolve({getTracks:()=>[{stop}]} as unknown as MediaStream));
  expect(stop).toHaveBeenCalledOnce();
});
test("socket sends only one frame until the server replies",()=>{
  let ws!:FakeSocket;
  class FakeSocket {
    static OPEN=1;readyState=1;bufferedAmount=0;
    onmessage?:(event:{data:string})=>void;onerror?:()=>void;onclose?:()=>void;
    send=vi.fn();close=vi.fn();
    constructor(){ws=this;}
  }
  vi.stubGlobal("WebSocket",FakeSocket);
  const result=vi.fn(),error=vi.fn(),connection=createLiveSocket(result,error);
  expect(connection.sendFrame(1,"abc")).toBe(true);
  expect(connection.sendFrame(2,"abc")).toBe(false);
  ws.onmessage?.({data:JSON.stringify({sequence:1})});
  expect(connection.sendFrame(3,"abc")).toBe(true);
  expect(ws.send).toHaveBeenCalledTimes(2);
  connection.close();
});
