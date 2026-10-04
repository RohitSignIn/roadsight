import { render, screen } from "@testing-library/react";
import { RuntimeStatus } from "../src/components/RuntimeStatus";

test("shows a ready CPU runtime", () => {
  render(<RuntimeStatus health={{ ready: true, device: "cpu", model: "best.pt" }} />);
  expect(screen.getByText(/model ready/i)).toBeInTheDocument();
  expect(screen.getByText(/cpu/i)).toBeInTheDocument();
});

test("shows a safe unavailable state", () => {
  render(<RuntimeStatus health={{ ready: false, message: "Model unavailable" }} />);
  expect(screen.getByText(/model unavailable/i)).toBeInTheDocument();
});
