'use client';

import { useRef, useState } from 'react';
import { Button } from "@/app/components/ui/button";
import { Upload } from "lucide-react";

export default function FileUpload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null); // Ref to access the file input

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]; // Get the first selected file
    if (file) {
      setSelectedFile(file);
      console.log('File selected:', file);
    }
  };

  const handleButtonClick = () => {
    // Programmatically click the hidden file input
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileUpload = () => {
    if (selectedFile) {
      console.log('Uploading file:', selectedFile);
      // Perform file upload action here (e.g., send it to a backend API)
    }
  };

  return (
    <div>
      <input
        ref={fileInputRef}
        id="file-upload"
        type="file"
        accept="application/pdf" // Specify PDF files
        onChange={handleFileChange}
        className="hidden" // Hide the input field
      />
      <Button variant="outline" onClick={handleButtonClick}>
        Select File
      </Button>
      
      {/* Display the selected file name below the button */}
      {selectedFile && (
        <div className="mt-2 text-sm text-gray-600">
          Selected file: {selectedFile.name}
        </div>
      )}

      {/* Button to trigger file upload once a file is selected */}
      {selectedFile && (
        <Button onClick={handleFileUpload} className="mt-4">
          <Upload className="h-4 w-4 mr-2" />
          Upload
        </Button>
      )}
    </div>
  );
}
