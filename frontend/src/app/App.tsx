import { useEffect,useState } from "react";
import { NavLink,Outlet } from "react-router-dom";
import { CarFront } from "lucide-react";
import { apiClient } from "../api/http";
import type { Health } from "../types/api";

export function App(){const[health,setHealth]=useState<Health|null>(null);useEffect(()=>{apiClient.health().then(setHealth).catch(()=>setHealth({ready:false,message:"Model unavailable"}))},[]);return <div className="app"><nav><NavLink to="/" className="brand"><span><CarFront/></span>RoadSight</NavLink><div><NavLink to="/">Overview</NavLink><NavLink to="/image">Image</NavLink><NavLink to="/video">Video</NavLink><NavLink to="/live">Live</NavLink></div></nav><main><Outlet context={{health}}/></main><footer>Runs locally · Uploaded files are temporary</footer></div>}
