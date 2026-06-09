import React, { useState } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("lucide-react", () => ({
  X: () => <span data-testid="icon-x" aria-label="remove">×</span>,
}));

import TagInput from "@/components/builder/TagInput";

function TagInputWrapper({
  initialTags = [] as string[],
  maxTags = 30,
  onChange: externalOnChange,
}: {
  initialTags?: string[];
  maxTags?: number;
  onChange?: (tags: string[]) => void;
}) {
  const [tags, setTags] = useState<string[]>(initialTags);
  return (
    <TagInput
      tags={tags}
      onChange={(newTags) => {
        setTags(newTags);
        externalOnChange?.(newTags);
      }}
      maxTags={maxTags}
      placeholder="Type and press Enter…"
    />
  );
}

describe("TagInput", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the input field", () => {
    render(<TagInputWrapper />);
    const input = screen.getByPlaceholderText("Type and press Enter…");
    expect(input).toBeTruthy();
  });

  it("renders existing tags", () => {
    render(<TagInputWrapper initialTags={["Python", "React", "Docker"]} />);
    expect(screen.getByText("Python")).toBeTruthy();
    expect(screen.getByText("React")).toBeTruthy();
    expect(screen.getByText("Docker")).toBeTruthy();
  });

  it("adds a tag on Enter key press", async () => {
    const onChange = vi.fn();
    render(<TagInputWrapper onChange={onChange} />);

    const input = screen.getByRole("textbox");
    await userEvent.type(input, "TypeScript");
    await userEvent.keyboard("{Enter}");

    expect(onChange).toHaveBeenCalledWith(["TypeScript"]);
  });

  it("adds a tag on comma key press", async () => {
    const onChange = vi.fn();
    render(<TagInputWrapper onChange={onChange} />);

    const input = screen.getByRole("textbox");
    await userEvent.type(input, "Kubernetes,");

    expect(onChange).toHaveBeenCalledWith(["Kubernetes"]);
  });

  it("clears the input after adding a tag", async () => {
    render(<TagInputWrapper />);

    const input = screen.getByRole("textbox") as HTMLInputElement;
    await userEvent.type(input, "AWS");
    await userEvent.keyboard("{Enter}");

    expect(input.value).toBe("");
  });

  it("removes a tag when X button is clicked", async () => {
    const onChange = vi.fn();
    render(<TagInputWrapper initialTags={["Python", "Go"]} onChange={onChange} />);

    const removeButtons = screen.getAllByTestId("icon-x");
    
    await userEvent.click(removeButtons[0]);

    expect(onChange).toHaveBeenCalledWith(["Go"]);
  });

  it("does not add duplicate tags (case-insensitive)", async () => {
    const onChange = vi.fn();
    render(<TagInputWrapper initialTags={["Python"]} onChange={onChange} />);

    const input = screen.getByRole("textbox");
    await userEvent.type(input, "python");
    await userEvent.keyboard("{Enter}");

    if (onChange.mock.calls.length > 0) {
      const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1];
      const tagLower = lastCall[0].map((t: string) => t.toLowerCase());
      const pythonCount = tagLower.filter((t: string) => t === "python").length;
      expect(pythonCount).toBe(1);
    }
  });

  it("enforces maxTags limit and does not add beyond it", async () => {
    const onChange = vi.fn();
    const maxTags = 3;
    render(
      <TagInputWrapper
        initialTags={["A", "B", "C"]}
        maxTags={maxTags}
        onChange={onChange}
      />,
    );

    const input = screen.getByRole("textbox");
    await userEvent.type(input, "D");
    await userEvent.keyboard("{Enter}");

    expect(onChange).not.toHaveBeenCalled();
  });

  it("removes the last tag when Backspace is pressed on empty input", async () => {
    const onChange = vi.fn();
    render(<TagInputWrapper initialTags={["Python", "Go"]} onChange={onChange} />);

    const input = screen.getByRole("textbox");
    await userEvent.click(input);
    await userEvent.keyboard("{Backspace}");

    expect(onChange).toHaveBeenCalledWith(["Python"]);
  });

  it("handles comma-separated input to add multiple tags at once", async () => {
    const onChange = vi.fn();
    render(<TagInputWrapper onChange={onChange} />);

    const input = screen.getByRole("textbox");
    
    await userEvent.type(input, "Redis, MongoDB");
    await userEvent.tab(); 

    expect(onChange).toHaveBeenCalled();
  });

  it("shows 'Add more...' placeholder when tags exist", () => {
    render(<TagInputWrapper initialTags={["Python"]} />);
    
    const input = screen.getByRole("textbox") as HTMLInputElement;
    expect(input.placeholder).toBe("Add more…");
  });

  it("trims whitespace from tag names", async () => {
    const onChange = vi.fn();
    render(<TagInputWrapper onChange={onChange} />);

    const input = screen.getByRole("textbox");
    await userEvent.type(input, "  AWS  ");
    await userEvent.keyboard("{Enter}");

    expect(onChange).toHaveBeenCalledWith(["AWS"]);
  });
});
