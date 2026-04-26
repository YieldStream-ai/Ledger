import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Image } from "lucide-react";
import { clsx } from "clsx";

interface DropZoneProps {
  onFilesAdded: (files: File[]) => void;
}

export function DropZone({ onFilesAdded }: DropZoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) onFilesAdded(accepted);
    },
    [onFilesAdded]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/tiff": [".tiff", ".tif"],
    },
    maxFiles: 20,
    maxSize: 315 * 1024 * 1024,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        "flex flex-col items-center justify-center rounded-xl border-2 border-dashed transition-colors cursor-pointer flex-1",
        isDragActive
          ? "border-blue-400 bg-blue-50"
          : "border-gray-300 bg-gray-50/50 hover:border-gray-400 hover:bg-gray-50"
      )}
    >
      <input {...getInputProps()} />
      <Upload
        className={clsx(
          "w-10 h-10 mb-4",
          isDragActive ? "text-blue-500" : "text-gray-400"
        )}
      />
      <p className="text-base font-medium text-gray-700">
        {isDragActive ? "Drop files here" : "Drag files here to upload"}
      </p>
      <p className="text-sm text-gray-500 mt-1">Up to 20 files, 315 MB total</p>

      <div className="flex items-center gap-6 mt-8 text-xs text-gray-500">
        <span className="flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5" />
          PDF
        </span>
        <span className="flex items-center gap-1.5">
          <Image className="w-3.5 h-3.5" />
          PNG, JPG, TIFF
        </span>
      </div>
    </div>
  );
}
