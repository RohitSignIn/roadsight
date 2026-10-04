import { render,screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { LivePage } from "../src/features/live/LivePage";

test("starts and stops camera tracks",async()=>{
 const stop=vi.fn();
 const getUserMedia=vi.fn().mockResolvedValue({getTracks:()=>[{stop}]});
 Object.defineProperty(navigator,"mediaDevices",{value:{getUserMedia},configurable:true});
 render(<LivePage socketFactory={()=>({close:vi.fn(),sendFrame:vi.fn()})}/>);
 await userEvent.click(screen.getByRole("button",{name:/start camera/i}));
 expect(getUserMedia).toHaveBeenCalled();
 await userEvent.click(screen.getByRole("button",{name:/stop camera/i}));
 expect(stop).toHaveBeenCalled();
});
