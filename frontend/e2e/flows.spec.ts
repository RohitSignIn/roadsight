import { test,expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { mkdirSync,statSync } from "node:fs";
import path from "node:path";

test.beforeAll(()=>{
  mkdirSync("test-results/fixtures",{recursive:true});
  execFileSync(path.resolve("../.venv/Scripts/python.exe"),["-c",
    "import cv2,numpy as np; p='test-results/fixtures/'; f=np.zeros((48,64,3),dtype=np.uint8); cv2.imwrite(p+'image.jpg',f); w=cv2.VideoWriter(p+'clip.mp4',cv2.VideoWriter_fourcc(*'mp4v'),10,(64,48)); [w.write(f) for _ in range(4)]; w.release()"]);
});
test("real checkpoint image export",async({page,request})=>{
  expect((await (await request.get("/api/health")).json()).ready).toBe(true);
  await page.goto("/image");
  await page.getByLabel("Choose image").setInputFiles("test-results/fixtures/image.jpg");
  await page.getByRole("button",{name:"Detect vehicles"}).click();
  await expect(page.getByAltText("Annotated detection result")).toBeVisible();
  const download=page.waitForEvent("download");
  await page.getByRole("link",{name:"Download ZIP"}).click();
  expect((await download).suggestedFilename()).toContain(".zip");
});
test("video size validation, H264 preview and ZIP",async({page})=>{
  await page.goto("/video");
  await page.getByLabel("Choose video").setInputFiles({name:"large.mp4",mimeType:"video/mp4",buffer:Buffer.alloc(10*1024*1024+1)});
  await expect(page.getByRole("alert")).toContainText("10 MB");
  await page.getByLabel("Choose video").setInputFiles("test-results/fixtures/clip.mp4");
  await page.getByRole("button",{name:"Process video"}).click();
  const video=page.getByLabel("Processed video");
  await expect(video).toBeVisible();
  await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.readyState)).toBeGreaterThanOrEqual(2);
  const download=page.waitForEvent("download");
  await page.getByRole("link",{name:"Download results"}).click();
  expect((await download).suggestedFilename()).toContain(".zip");
});
test("synthetic webcam through Vite proxy records and saves WebM",async({page})=>{
  await page.goto("/live");
  await page.getByRole("button",{name:"Start camera"}).click();
  await expect(page.getByText(/inference FPS/)).toBeVisible();
  await page.getByRole("button",{name:"Record",exact:true}).click();
  await expect(page.getByRole("button",{name:"Stop recording"})).toBeVisible();
  await expect.poll(()=>page.locator("canvas").evaluate((c:HTMLCanvasElement)=>c.width)).toBeGreaterThan(100);
  await page.waitForTimeout(1200);
  await page.getByRole("button",{name:"Stop recording"}).click();
  const download=page.waitForEvent("download");
  await page.getByRole("button",{name:"Save WebM"}).click();
  const recording=await download;
  expect(recording.suggestedFilename()).toMatch(/\.webm$/);
  expect(statSync((await recording.path())!).size).toBeGreaterThan(100);
  await page.getByRole("button",{name:"Stop camera"}).click();
  await expect(page.getByRole("button",{name:"Start camera"})).toBeVisible();
});
