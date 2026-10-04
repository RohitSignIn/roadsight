import type { VehicleRecord } from "../../types/api";
const columns:(keyof VehicleRecord)[]=["vehicle_id","vehicle_type","color","first_seen","last_seen","duration_seconds","direction","average_confidence","maximum_confidence","relative_size"];
function cell(value:string|number){const text=typeof value==="number"&&!Number.isInteger(value)?value.toFixed(3):String(value);return /[",\n]/.test(text)?`"${text.replaceAll('"','""')}"`:text}
export function buildSessionCsv(records:VehicleRecord[]){return [columns.join(","),...records.map(record=>columns.map(key=>cell(record[key])).join(","))].join("\n")}
export function buildSessionJson(records:VehicleRecord[],metadata:Record<string,unknown>){return JSON.stringify({metadata,vehicles:records},null,2)}
export function downloadText(name:string,text:string,type:string){const url=URL.createObjectURL(new Blob([text],{type}));const anchor=document.createElement("a");anchor.href=url;anchor.download=name;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),0)}
