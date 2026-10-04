import { useState } from "react";
import type { VehicleRecord } from "../types/api";
export function VehicleTable({vehicles}:{vehicles:VehicleRecord[]}) {
  const [filter,setFilter]=useState("");
  const counts=vehicles.reduce<Record<string,number>>((all,v)=>({...all,[v.vehicle_type]:(all[v.vehicle_type]??0)+1}),{});
  const visible=vehicles.filter(v=>[v.vehicle_type,v.color,v.direction].join(" ").toLowerCase().includes(filter.toLowerCase()));
  return <div>
    <p>{vehicles.length} unique vehicles{Object.entries(counts).map(([name,count])=><span key={name}> · {name}: {count}</span>)}</p>
    <label>Filter vehicles <input value={filter} onChange={e=>setFilter(e.target.value)} placeholder="Type, color or direction"/></label>
    {!vehicles.length?<p className="empty">No vehicles detected.</p>:<div className="table-wrap"><table><thead><tr><th>ID</th><th>Type</th><th>Color</th><th>Direction</th><th>First seen (s)</th><th>Last seen (s)</th><th>Confidence</th></tr></thead><tbody>{visible.map(v=><tr key={v.vehicle_id}><td>#{v.vehicle_id}</td><td>{v.vehicle_type}</td><td>{v.color}</td><td>{v.direction}</td><td>{v.first_seen.toFixed(2)}</td><td>{v.last_seen.toFixed(2)}</td><td>{Math.round(v.average_confidence*100)}%</td></tr>)}</tbody></table></div>}
  </div>;
}
