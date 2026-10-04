import { createBrowserRouter, useOutletContext } from "react-router-dom";
import { App } from "./App";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { ImagePage } from "../features/image/ImagePage";
import { VideoPage } from "../features/video/VideoPage";
import type { Health } from "../types/api";
import { LivePage } from "../features/live/LivePage";

function Dashboard(){const{health}=useOutletContext<{health:Health|null}>();return <DashboardPage health={health}/>}
export const router=createBrowserRouter([{path:"/",element:<App/>,children:[{index:true,element:<Dashboard/>},{path:"image",element:<ImagePage/>},{path:"video",element:<VideoPage/>},{path:"live",element:<LivePage/>}]}]);
