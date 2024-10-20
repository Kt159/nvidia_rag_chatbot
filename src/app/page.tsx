'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from "@/app/components/ui/button"
import { Input } from "@/app/components/ui/input"
import { Card, CardContent } from "@/app/components/ui/card"
import { ScrollArea } from "@/app/components/ui/scroll-area"
import { Upload, Trash2, Send, FileText } from "lucide-react"

interface Document {
  id: string
  name: string
}

type Message = {
  role: 'user' | 'bot';
  content: string;
};

export default function RAGChatbot() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', content: "Hello! I'm your AI assistant. How can I help you today?" }
  ])
  const [input, setInput] = useState('')
  const [documents, setDocuments] = useState<Document[]>([])
  const [sidebarWidth, setSidebarWidth] = useState(300)
  const sidebarRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return
      const newWidth = e.clientX
      if (newWidth > 200 && newWidth < window.innerWidth - 400) {
        setSidebarWidth(newWidth)
      }
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging])

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await fetch('/api/minio')
      if (response.ok) {
        const data = await response.json()
        setDocuments(data.map((doc: string) => ({ id: doc, name: doc })))
      } else {
        console.error('Failed to fetch documents')
      }
    } catch (error) {
      console.error('Error fetching documents:', error)
    }
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const newMessages: Message[] = [...messages, { role: 'user', content: input }]
    setMessages(newMessages)
    setInput('')

    // Simulating API call
    setTimeout(() => {
      setMessages([...newMessages, { role: 'bot', content: "I've received your message. How can I assist you further?" }])
    }, 1000)
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || file.type !== 'application/pdf') {
      alert('Please upload a PDF file.')
      return
    }
    setSelectedFile(file);
    console.log('File selected:', file);
  };

  const handleButtonClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileUpload = async () => {
    if (selectedFile) {
      setIsUploading(true);
      console.log('Uploading file:', selectedFile);
      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const response = await fetch('/api/minio', {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          console.log('File uploaded successfully');
          setSelectedFile(null);
          fetchDocuments();
        } else {
          const errorText = await response.text();
          console.error('File upload failed:', errorText);
        }
      } catch (error) {
        console.error('Error uploading file:', error);
      } finally {
        setIsUploading(false);
      }
    }
  };

  const handleFileDelete = async (documentId: string) => {
    try {
      const response = await fetch(`/api/minio?filename=${documentId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setDocuments(documents.filter(doc => doc.id !== documentId));
      } else {
        console.error('Failed to delete document');
      }
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <div 
        ref={sidebarRef}
        className="bg-white border-r relative"
        style={{ width: `${sidebarWidth}px` }}
      >
        <div className="p-4">
          <h2 className="text-lg font-semibold mb-4">Uploaded Documents</h2>
          <div className="mb-4 flex items-center space-x-2">
            <Input
              ref={fileInputRef}
              id="file-upload"
              type="file"
              accept="application/pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            <Button onClick={handleButtonClick} variant="outline">
              Select PDF
            </Button>
            {selectedFile && !isUploading && (
              <Button onClick={handleFileUpload}>
                <Upload className="h-4 w-4 mr-2" />
                Upload
              </Button>
            )}
          </div>
          {selectedFile && (
            <div className="mt-2 text-sm text-gray-600">
              Selected file: {selectedFile.name}
            </div>
          )}
          <ScrollArea className="h-[calc(100vh-12rem)]">
            {documents.map((doc) => (
              <div key={doc.id} className="flex justify-between items-center mb-2 p-2 bg-gray-50 rounded">
                <div className="flex items-center">
                  <FileText className="h-4 w-4 mr-2 text-blue-500" />
                  <span className="truncate">{doc.name}</span>
                </div>
                <Button variant="ghost" size="icon" onClick={() => handleFileDelete(doc.id)}>
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </div>
            ))}
          </ScrollArea>
        </div>
        <div 
          className="absolute top-0 right-0 w-1 h-full cursor-col-resize bg-gray-300 hover:bg-gray-400"
          onMouseDown={() => setIsDragging(true)}
        />
      </div>
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b p-4">
          <h1 className="text-2xl font-bold">RAG Chatbot</h1>
        </header>
        <main className="flex-1 overflow-hidden">
          <Card className="h-full flex flex-col m-4">
            <CardContent className="flex-1 overflow-hidden flex flex-col p-4">
              <ScrollArea className="flex-1 pr-4">
                {messages.map((message, index) => (
                  <div key={index} className={`mb-4 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                    <span className={`inline-block p-2 rounded-lg ${message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}>
                      {message.content}
                    </span>
                  </div>
                ))}
              </ScrollArea>
              <div className="pt-4 border-t">
                <div className="flex space-x-2">
                  <Input
                    type="text"
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  />
                  <Button onClick={handleSend}>
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  )
}