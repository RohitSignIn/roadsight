import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir:"./e2e", timeout:60000, workers:1,
  use:{baseURL:"http://127.0.0.1:5189",channel:"msedge",headless:true,
    launchOptions:{args:["--use-fake-ui-for-media-stream","--use-fake-device-for-media-stream"]}},
  webServer:[
    {command:'..\\.venv\\Scripts\\python.exe -m uvicorn backend.app.main:app --app-dir .. --port 8011',url:"http://127.0.0.1:8011/api/health",timeout:120000,reuseExistingServer:false},
    {command:"npm run dev -- --host 127.0.0.1 --port 5189 --mode e2e",url:"http://127.0.0.1:5189",reuseExistingServer:false},
  ],
});
