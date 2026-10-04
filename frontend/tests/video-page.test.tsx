import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { VideoPage } from "../src/features/video/VideoPage";

test("rejects videos larger than 10 MB before upload", async () => {
  const submit = vi.fn();
  render(<VideoPage submitVideo={submit} getJob={vi.fn()} cancelJob={vi.fn()} />);
  const file = new File([new Uint8Array(10 * 1024 * 1024 + 1)], "large.mp4", {type:"video/mp4"});
  await userEvent.upload(screen.getByLabelText(/choose video/i), file);
  expect(screen.getByText(/10 mb or smaller/i)).toBeInTheDocument();
  expect(submit).not.toHaveBeenCalled();
});

test("polls a submitted job and offers download", async () => {
  vi.useFakeTimers({shouldAdvanceTime:true});
  const submit = vi.fn().mockResolvedValue({id:"job-1",status:"queued",progress:0,download_ready:false});
  const getJob = vi.fn().mockResolvedValue({id:"job-1",status:"completed",progress:1,download_ready:true});
  render(<VideoPage submitVideo={submit} getJob={getJob} cancelJob={vi.fn()} pollInterval={1} />);
  await userEvent.upload(screen.getByLabelText(/choose video/i), new File(["video"], "clip.mp4", {type:"video/mp4"}));
  await userEvent.click(screen.getByRole("button", {name:/process video/i}));
  expect(await screen.findByRole("link", {name:/download results/i})).toBeInTheDocument();
  vi.useRealTimers();
});
