"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { Upload, FileText, X, CheckCircle, Loader2 } from "lucide-react";
import { uploadResume, ApiError } from "@/lib/api";
import type { UploadResumeResponse } from "@/types";

const ACCEPTED = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "application/msword": [".doc"],
};

type Stage = "idle" | "uploading" | "done" | "error";

interface Props {
  onSuccess?: (result: UploadResumeResponse) => void;
}

export default function UploadZone({ onSuccess }: Props) {
  const { getToken } = useAuth();
  const [stage, setStage] = useState<Stage>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<UploadResumeResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  const reset = () => {
    setStage("idle");
    setFile(null);
    setProgress(0);
    setResult(null);
    setErrorMsg("");
  };

  const handleUpload = useCallback(
    async (accepted: File[]) => {
      const f = accepted[0];
      if (!f) return;

      if (f.size > 10 * 1024 * 1024) {
        toast.error("File too large. Maximum size is 10 MB.");
        return;
      }

      setFile(f);
      setStage("uploading");
      setProgress(10);

      try {
        const token = await getToken();
        if (!token) throw new Error("Not authenticated");

        const ticker = setInterval(
          () => setProgress((p) => Math.min(p + 15, 85)),
          400,
        );

        const res = await uploadResume(f, token);
        clearInterval(ticker);
        setProgress(100);
        setResult(res);
        setStage("done");
        toast.success("Resume uploaded successfully!");
        onSuccess?.(res);
      } catch (err) {
        const msg =
          err instanceof ApiError ? err.detail : "Upload failed. Please try again.";
        setErrorMsg(msg);
        setStage("error");
        toast.error(msg);
      }
    },
    [getToken, onSuccess],
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDropAccepted: handleUpload,
    onDropRejected: () => toast.error("Only PDF or DOCX files are accepted."),
    accept: ACCEPTED,
    maxFiles: 1,
    disabled: stage === "uploading",
  });

  if (stage === "done" && result) {
    return (
      <div className="flex flex-col items-center gap-4 rounded-xl border border-[var(--pf-border-light)] bg-[var(--pf-surface)] p-10 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[rgba(0,212,80,0.12)]">
          <CheckCircle className="h-8 w-8 text-green-400" />
        </div>
        <div>
          <p className="text-lg font-semibold text-[var(--pf-text)]">Upload complete</p>
          <p className="mt-1 text-sm text-[var(--pf-muted)]">{result.filename}</p>
        </div>
        <p className="text-sm text-[var(--pf-muted)]">
          Resume ID: <span className="font-mono text-[var(--pf-text)]">{result.resume_id}</span>
        </p>
        <button
          onClick={reset}
          className="mt-2 rounded-lg border border-[var(--pf-border-light)] px-4 py-2 text-sm text-[var(--pf-muted)] hover:border-[rgba(108,99,255,0.5)] hover:text-[var(--pf-text)] transition-colors"
        >
          Upload another
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`relative flex cursor-pointer flex-col items-center gap-4 rounded-xl border-2 border-dashed p-12 text-center transition-all ${
          isDragReject
            ? "border-red-500 bg-[rgba(255,77,77,0.05)]"
            : isDragActive
              ? "border-[var(--pf-accent)] bg-[var(--pf-border-subtle)]"
              : stage === "error"
                ? "border-red-500/40 bg-[rgba(255,77,77,0.03)]"
                : "border-[var(--pf-border-light)] bg-[var(--pf-surface)] hover:border-[rgba(108,99,255,0.45)] hover:bg-[rgba(108,99,255,0.04)]"
        }`}
      >
        <input {...getInputProps()} />

        {stage === "uploading" ? (
          <>
            <Loader2 className="h-10 w-10 animate-spin text-[var(--pf-accent)]" />
            <div className="w-full max-w-xs space-y-2">
              <div className="flex justify-between text-sm text-[var(--pf-muted)]">
                <span className="truncate max-w-[200px]">{file?.name}</span>
                <span>{progress}%</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--pf-accent-soft)]">
                <div
                  className="h-full rounded-full bg-[var(--pf-accent)] transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </>
        ) : stage === "error" ? (
          <>
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[rgba(255,77,77,0.1)]">
              <X className="h-7 w-7 text-red-400" />
            </div>
            <div>
              <p className="font-semibold text-red-400">Upload failed</p>
              <p className="mt-1 text-sm text-[var(--pf-muted)]">
                {typeof errorMsg === "string" ? errorMsg : "Upload failed. Please try again."}
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                reset();
              }}
              className="rounded-lg border border-[var(--pf-border-light)] px-4 py-2 text-sm text-[var(--pf-muted)] hover:text-[var(--pf-text)] transition-colors"
            >
              Try again
            </button>
          </>
        ) : (
          <>
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--pf-border-dim)]">
              {isDragActive ? (
                <FileText className="h-7 w-7 text-[var(--pf-accent)]" />
              ) : (
                <Upload className="h-7 w-7 text-[var(--pf-accent)]" />
              )}
            </div>
            <div>
              <p className="text-base font-semibold text-[var(--pf-text)]">
                {isDragActive ? "Drop it here" : "Drag & drop your resume"}
              </p>
              <p className="mt-1 text-sm text-[var(--pf-muted)]">
                or{" "}
                <span className="text-[var(--pf-accent)] underline-offset-2 hover:underline">
                  browse files
                </span>
              </p>
            </div>
            <p className="text-xs text-[var(--pf-muted)]">PDF or DOCX · max 10 MB</p>
          </>
        )}
      </div>
    </div>
  );
}
