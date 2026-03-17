"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";

// react-pdf must be dynamically imported to avoid SSR errors
const Document = dynamic(() => import("react-pdf").then((mod) => mod.Document), {
  ssr: false,
});
const Page = dynamic(() => import("react-pdf").then((mod) => mod.Page), {
  ssr: false,
});

export interface PdfPreviewProps {
  /**
   * URL or data URI pointing to the PDF file.
   * Example: data:application/pdf;base64,... or a blob URL
   */
  fileUrl: string;
  page?: number;
  scale?: number;
}

export function PdfPreview({ fileUrl, page = 1, scale = 1.0 }: PdfPreviewProps) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const setupPdfWorker = async () => {
      try {
        const pdfModule = await import("react-pdf");
        if (isMounted && pdfModule.pdfjs) {
          // Use jsdelivr CDN which is more reliable
          pdfModule.pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfModule.pdfjs.version}/build/pdf.worker.min.js`;
        }
      } catch (err) {
        console.error("Failed to setup PDF worker:", err);
      }
    };

    setupPdfWorker();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-slate-900">PDF Preview</div>
        {numPages ? (
          <div className="text-xs text-slate-500">{numPages} หน้า</div>
        ) : null}
      </div>
      {error ? (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      ) : (
        <div className="mt-3">
          <Document
            file={fileUrl}
            onLoadSuccess={({ numPages }) => {
              setNumPages(numPages);
            }}
            onLoadError={(err) => {
              setError("ไม่สามารถโหลด PDF ได้");
              console.error(err);
            }}
            options={{ cMapUrl: "cmaps/", cMapPacked: true }}
          >
            <Page pageNumber={page} scale={scale} />
          </Document>
        </div>
      )}
    </div>
  );
}
