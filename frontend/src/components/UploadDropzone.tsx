import { useCallback, useRef, useState } from "react";
import type { DragEvent } from "react";
import { ALLOWED_UPLOAD_MIME_TYPES, MAX_UPLOAD_SIZE_BYTES } from "@shared/types";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

function formatBytes(bytes: number): string {
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadDropzone({ onFileSelected, disabled }: UploadDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = useCallback(
    (file: File) => {
      if (!ALLOWED_UPLOAD_MIME_TYPES.includes(file.type)) {
        setValidationError("Only PDF files are supported.");
        return;
      }
      if (file.size > MAX_UPLOAD_SIZE_BYTES) {
        setValidationError(`File is too large. Maximum size is ${formatBytes(MAX_UPLOAD_SIZE_BYTES)}.`);
        return;
      }
      setValidationError(null);
      onFileSelected(file);
    },
    [onFileSelected],
  );

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;
    const file = e.dataTransfer.files?.[0];
    if (file) validateAndSelect(file);
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        aria-label="Upload resume PDF — drag and drop, or activate to browse files"
        onKeyDown={(e) => {
          if (disabled) return;
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-14 text-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 focus-visible:ring-offset-2 ${
          disabled
            ? "cursor-not-allowed border-ink-200 bg-ink-100"
            : isDragOver
              ? "border-accent-500 bg-accent-50"
              : "border-ink-200 hover:border-accent-400 hover:bg-accent-50/30"
        }`}
      >
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-ink-900 font-mono text-sm text-white">
          ↑
        </span>
        <p className="text-sm font-medium text-ink-900">
          {isDragOver ? "Drop your resume here" : "Drag & drop your resume PDF"}
        </p>
        <p className="text-xs text-ink-500">
          or click to browse — PDF only, up to {formatBytes(MAX_UPLOAD_SIZE_BYTES)}
        </p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          disabled={disabled}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) validateAndSelect(file);
            e.target.value = "";
          }}
        />
      </div>
      {validationError && <p className="mt-2 text-sm text-danger">{validationError}</p>}
    </div>
  );
}
