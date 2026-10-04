import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ImagePage } from "../src/features/image/ImagePage";

test("uploads an image and displays detected vehicles", async () => {
  const detect = vi.fn().mockResolvedValue({annotated_image_base64:"abc",vehicles:[{vehicle_id:1,vehicle_type:"car",color:"red",direction:"right",first_seen:0,last_seen:0,duration_seconds:0,average_confidence:.9,maximum_confidence:.9,relative_size:.2}]});
  render(<ImagePage detectImage={detect} />);
  const file = new File(["image"], "car.jpg", {type:"image/jpeg"});
  await userEvent.upload(screen.getByLabelText(/choose image/i), file);
  await userEvent.click(screen.getByRole("button", {name:/detect vehicles/i}));
  expect(await screen.findByText("car")).toBeInTheDocument();
  expect(screen.getByRole("link", {name:/download image/i})).toBeInTheDocument();
});
