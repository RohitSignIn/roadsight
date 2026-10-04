export type Health = { ready: boolean; device?: string | null; model?: string | null; message?: string | null };
export type VehicleRecord = {vehicle_id:number;vehicle_type:string;color:string;first_seen:number;last_seen:number;duration_seconds:number;direction:string;average_confidence:number;maximum_confidence:number;relative_size:number};
export type ImageResult = { annotated_image_base64: string; vehicles: VehicleRecord[]; download_url?:string };
export type JobStatus = "queued"|"processing"|"completed"|"failed"|"cancelled"|"expired";
export type VideoJob = { id:string; status:JobStatus; progress:number; error?:string|null; download_ready:boolean; vehicles?:VehicleRecord[]; preview_url?:string|null };
