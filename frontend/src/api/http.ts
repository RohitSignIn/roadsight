import type { Health, ImageResult, VideoJob } from "../types/api";

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  health: () => fetch("/api/health").then(parse<Health>),
  detectImage: (file: File) => { const data=new FormData(); data.append("file",file); return fetch("/api/images/detect",{method:"POST",body:data}).then(parse<ImageResult>); },
  submitVideo: (file: File) => { const data=new FormData(); data.append("file",file); return fetch("/api/videos",{method:"POST",body:data}).then(parse<VideoJob>); },
  getJob: (id:string) => fetch(`/api/videos/${id}`).then(parse<VideoJob>),
  cancelJob: (id:string) => fetch(`/api/videos/${id}`,{method:"DELETE"}).then(parse<VideoJob>),
  downloadUrl: (id:string) => `/api/videos/${id}/download`,
};
