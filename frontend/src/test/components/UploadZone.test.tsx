import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    isSignedIn: true,
    isLoaded: true,
    getToken: vi.fn().mockResolvedValue("mock-token"),
  }),
}));

vi.mock("@/lib/api", () => ({
  uploadResume: vi.fn(),
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public detail: string,
    ) {
      super(detail);
      this.name = "ApiError";
    }
  },
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("lucide-react", () => ({
  Upload: () => <span data-testid="icon-upload">upload</span>,
  FileText: () => <span data-testid="icon-file">file</span>,
  X: () => <span data-testid="icon-x">x</span>,
  CheckCircle: () => <span data-testid="icon-check">check</span>,
  Loader2: () => <span data-testid="icon-loader">loading</span>,
}));

import UploadZone from "@/components/upload/UploadZone";
import { uploadResume } from "@/lib/api";

const mockUploadResume = vi.mocked(uploadResume);

function createPdfFile(name = "resume.pdf"): File {
  return new File(["%PDF-1.4 fake content"], name, {
    type: "application/pdf",
  });
}

function createTextFile(name = "document.txt"): File {
  return new File(["plain text content"], name, { type: "text/plain" });
}

describe("UploadZone", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the drop zone with upload instructions", () => {
    render(<UploadZone />);
    expect(screen.getByText(/drag & drop your resume/i)).toBeTruthy();
    expect(screen.getByText(/PDF or DOCX/i)).toBeTruthy();
  });

  it("renders browse files link text", () => {
    render(<UploadZone />);
    expect(screen.getByText(/browse files/i)).toBeTruthy();
  });

  it("shows uploading state with file name when upload starts", async () => {
    
    mockUploadResume.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000)),
    );

    render(<UploadZone />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeTruthy();

    const file = createPdfFile("my_cv.pdf");
    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    await waitFor(() => {
      expect(screen.getByTestId("icon-loader")).toBeTruthy();
    });
  });

  it("shows success state and resume ID after successful upload", async () => {
    mockUploadResume.mockResolvedValue({
      resume_id: "test-resume-123",
      filename: "my_resume.pdf",
      message: "Upload successful",
    });

    render(<UploadZone />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = createPdfFile("my_resume.pdf");

    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    await waitFor(() => {
      expect(screen.getByText(/upload complete/i)).toBeTruthy();
    });
    expect(screen.getByText("test-resume-123")).toBeTruthy();
  });

  it("calls onSuccess callback after successful upload", async () => {
    const onSuccess = vi.fn();
    mockUploadResume.mockResolvedValue({
      resume_id: "cb-resume-456",
      filename: "resume.pdf",
      message: "Done",
    });

    render(<UploadZone onSuccess={onSuccess} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    await act(async () => {
      fireEvent.change(input, { target: { files: [createPdfFile()] } });
    });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1);
    });
  });

  it("shows error state when upload fails", async () => {
    const { ApiError } = await import("@/lib/api");
    mockUploadResume.mockRejectedValue(
      new (ApiError as any)(400, "Invalid file type"),
    );

    render(<UploadZone />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    await act(async () => {
      fireEvent.change(input, { target: { files: [createPdfFile()] } });
    });

    await waitFor(() => {
      expect(screen.getByText(/upload failed/i)).toBeTruthy();
    });
  });

  it("shows try again button after error", async () => {
    mockUploadResume.mockRejectedValue(new Error("Network error"));

    render(<UploadZone />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    await act(async () => {
      fireEvent.change(input, { target: { files: [createPdfFile()] } });
    });

    await waitFor(() => {
      
      const elements = screen.getAllByText(/try again/i);
      expect(elements.length).toBeGreaterThan(0);
    });
  });

  it("resets to idle state when try again is clicked", async () => {
    mockUploadResume.mockRejectedValue(new Error("Upload failed"));

    render(<UploadZone />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    await act(async () => {
      fireEvent.change(input, { target: { files: [createPdfFile()] } });
    });

    await waitFor(() => {
      expect(screen.getAllByText(/upload failed/i).length).toBeGreaterThan(0);
    });

    const tryAgainButton = screen.getByRole("button", { name: /try again/i });
    await act(async () => {
      fireEvent.click(tryAgainButton);
    });

    expect(screen.getByText(/drag & drop your resume/i)).toBeTruthy();
  });

  it("shows upload another button after success and resets on click", async () => {
    mockUploadResume.mockResolvedValue({
      resume_id: "done-123",
      filename: "done.pdf",
      message: "Done",
    });

    render(<UploadZone />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    await act(async () => {
      fireEvent.change(input, { target: { files: [createPdfFile()] } });
    });

    await waitFor(() => {
      expect(screen.getByText(/upload another/i)).toBeTruthy();
    });

    await act(async () => {
      fireEvent.click(screen.getByText(/upload another/i));
    });

    expect(screen.getByText(/drag & drop your resume/i)).toBeTruthy();
  });
});
