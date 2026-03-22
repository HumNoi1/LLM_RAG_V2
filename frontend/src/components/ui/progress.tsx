import React from "react";

interface ProgressProps {
  value: number;
  max?: number;
}

export const Progress: React.FC<ProgressProps> = ({ value, max = 100 }) => (
  <div className="w-full bg-gray-200 rounded-full h-4">
    <div
      className="bg-blue-500 h-4 rounded-full transition-all"
      style={{ width: `${Math.min(value, max)}%` }}
    />
  </div>
);
