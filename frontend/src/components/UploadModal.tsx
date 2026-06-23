"use client";

import { useState, useRef, DragEvent } from "react";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const [fuelFile, setFuelFile] = useState<File | null>(null);
  const [modelFile, setModelFile] = useState<File | null>(null);
  
  const [fuelDragActive, setFuelDragActive] = useState(false);
  const [modelDragActive, setModelDragActive] = useState(false);
  //what is const const?   
  // eslint-disable-next-line no-unused-vars
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const fuelInputRef = useRef<HTMLInputElement>(null);
  const modelInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDrag = (e: DragEvent, setDragActive: (val: boolean) => void) => {
    e.preventDefault();
    e.stopPropagation();
    //what is dragenter, dragover, and dragleave?
    // Drag Events:
    // - dragenter: Triggered when a dragged item enters a valid drop target.
    // - dragover: Triggered when a dragged item is being dragged over a valid drop target (fires continuously).
    // - dragleave: Triggered when a dragged item leaves a valid drop target.
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent, setFile: (f: File) => void, setDragActive: (val: boolean) => void) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, setFile: (f: File) => void) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!fuelFile || !modelFile) {
      setErrorMessage("Both Fuel Data and Model Data files are required.");
      setStatus("error");
      return;
    }

    setIsUploading(true);
    setStatus("idle");
    setErrorMessage("");

    const formData = new FormData();
    formData.append("fuelFile", fuelFile);
    formData.append("modelFile", modelFile);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (response.status === 409) {
        setErrorMessage("An update is already running. Please wait.");
        setStatus("error");
        setIsUploading(false);
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Upload failed");
      }

      setStatus("success");
      // Wait for toast to show, then refresh
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (err: any) {
      setErrorMessage(err.message || "An error occurred during upload.");
      setStatus("error");
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-[#020617]/80" 
        onClick={() => !isUploading && onClose()}
      />

      {/* Modal Surface */}
      <div className="relative w-full max-w-md bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
          <h2 className="text-[14px] font-semibold text-[var(--color-ink)] leading-tight tracking-[0.02em]">
            Upload Data
          </h2>
          <button 
            onClick={onClose}
            disabled={isUploading}
            className="text-[var(--color-ink-subtle)] hover:text-[var(--color-ink)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Close"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 4L4 12M4 4L12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 flex flex-col gap-6">
          {/* Fuel Data Zone */}
          <div className="flex flex-col gap-2">
            <span className="text-[12px] font-medium text-[var(--color-ink)]">Fuel Data Excel</span>
            <div 
              className={`relative flex flex-col items-center justify-center p-6 border transition-colors cursor-pointer rounded-sm ${
                fuelDragActive 
                  ? "border-[var(--color-ink-muted)] bg-[var(--color-bg)]" 
                  : "border-[var(--color-border)] hover:border-[var(--color-ink-subtle)] bg-[var(--color-surface)]"
              }`}
              onDragEnter={(e) => handleDrag(e, setFuelDragActive)}
              onDragLeave={(e) => handleDrag(e, setFuelDragActive)}
              onDragOver={(e) => handleDrag(e, setFuelDragActive)}
              onDrop={(e) => handleDrop(e, setFuelFile, setFuelDragActive)}
              onClick={() => fuelInputRef.current?.click()}
            >
              <input 
                ref={fuelInputRef}
                type="file" 
                accept=".xlsx,.xls" 
                className="hidden" 
                onChange={(e) => handleFileChange(e, setFuelFile)}
              />
              {fuelFile ? (
                <div className="flex items-center gap-2 text-[12px] text-[var(--color-ink)]">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                  <span className="truncate max-w-[200px]">{fuelFile.name}</span>
                </div>
              ) : (
                <span className="text-[12px] text-[var(--color-ink-subtle)]">
                  Drag and drop or <span className="text-[var(--color-ink)] underline decoration-[var(--color-border)] underline-offset-2">browse</span>
                </span>
              )}
            </div>
          </div>

          {/* Model Data Zone */}
          <div className="flex flex-col gap-2">
            <span className="text-[12px] font-medium text-[var(--color-ink)]">Model Data Excel</span>
            <div 
              className={`relative flex flex-col items-center justify-center p-6 border transition-colors cursor-pointer rounded-sm ${
                modelDragActive 
                  ? "border-[var(--color-ink-muted)] bg-[var(--color-bg)]" 
                  : "border-[var(--color-border)] hover:border-[var(--color-ink-subtle)] bg-[var(--color-surface)]"
              }`}
              onDragEnter={(e) => handleDrag(e, setModelDragActive)}
              onDragLeave={(e) => handleDrag(e, setModelDragActive)}
              onDragOver={(e) => handleDrag(e, setModelDragActive)}
              onDrop={(e) => handleDrop(e, setModelFile, setModelDragActive)}
              onClick={() => modelInputRef.current?.click()}
            >
              <input 
                ref={modelInputRef}
                type="file" 
                accept=".xlsx,.xls" 
                className="hidden" 
                onChange={(e) => handleFileChange(e, setModelFile)}
              />
              {modelFile ? (
                <div className="flex items-center gap-2 text-[12px] text-[var(--color-ink)]">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                  <span className="truncate max-w-[200px]">{modelFile.name}</span>
                </div>
              ) : (
                <span className="text-[12px] text-[var(--color-ink-subtle)]">
                  Drag and drop or <span className="text-[var(--color-ink)] underline decoration-[var(--color-border)] underline-offset-2">browse</span>
                </span>
              )}
            </div>
          </div>

          {/* Feedback Area */}
          <div className="min-h-[20px] flex items-center justify-center">
            {status === "error" && (
              <span className="text-[12px] text-red-400">{errorMessage}</span>
            )}
            {isUploading && (
              <div className="flex items-center gap-2 text-[12px] text-[var(--color-ink-muted)]">
                <svg className="animate-spin h-3.5 w-3.5 text-[var(--color-ink-subtle)]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Processing — this can take several minutes. Don&apos;t close this tab.</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-bg)] flex justify-end">
          <button
            onClick={handleUpload}
            disabled={isUploading || (!fuelFile && !modelFile)}
            className="px-4 py-2 bg-[var(--color-ink)] text-[var(--color-bg)] text-[12px] font-medium rounded-sm hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isUploading ? "Updating..." : "Update Dashboard"}
          </button>
        </div>
      </div>

      {/* Success Toast */}
      {status === "success" && (
        <div className="absolute top-6 left-1/2 -translate-x-1/2 bg-[var(--color-surface)] border border-[var(--color-accent-bev)] px-4 py-2 rounded-sm flex items-center gap-2 z-[60]">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-bev)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span className="text-[12px] font-medium text-[var(--color-ink)]">Upload successful. Refreshing...</span>
        </div>
      )}
    </div>
  );
}
