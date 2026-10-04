import { buildSessionCsv,buildSessionJson } from "../src/features/live/sessionReport";
import { selectSupportedMimeType } from "../src/features/live/useCanvasRecorder";
import { vi } from "vitest";

const records=[{vehicle_id:1,vehicle_type:'car,"sedan"',color:"red",first_seen:1.25,last_seen:3.5,duration_seconds:2.25,direction:"right",average_confidence:.8,maximum_confidence:.9,relative_size:.2}];

test("serializes one safely escaped CSV row per vehicle",()=>{
 const csv=buildSessionCsv(records);
 expect(csv.split("\n")).toHaveLength(2);
 expect(csv).toContain('"car,""sedan"""');
 expect(csv).toContain("1.250");
});

test("serializes session metadata and records as JSON",()=>{
 const body=JSON.parse(buildSessionJson(records,{source:"webcam"}));
 expect(body.metadata.source).toBe("webcam");
 expect(body.vehicles).toHaveLength(1);
});

test("selects the first supported WebM codec",()=>{
 const check=vi.fn((type:string)=>type.includes("vp8"));
 expect(selectSupportedMimeType(check)).toContain("vp8");
});
