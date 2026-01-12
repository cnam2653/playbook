import { useState, useRef } from 'react'
import { Upload, Video, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface VideoInputProps {
  onFileSelect: (file: File | null) => void
  onAnalysisStart: (analysisId: string) => void
}

const VideoInput: React.FC<VideoInputProps> = ({ onFileSelect, onAnalysisStart }) => {
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile)
    onFileSelect(selectedFile)

    // Create preview URL for the video
    const previewUrl = URL.createObjectURL(selectedFile)
    setVideoPreviewUrl(previewUrl)
  }

  const handleNewVideo = () => {
    setFile(null)
    setVideoPreviewUrl(null)
    onFileSelect(null)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.type.startsWith('video/')) {
      handleFileSelect(droppedFile)
    }
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      handleFileSelect(selectedFile)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    const formData = new FormData()
    formData.append('video', file)
    formData.append('sport', 'soccer') // Default to soccer

    try {
      const response = await fetch('http://localhost:5001/upload', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (response.ok) {
        onAnalysisStart(data.analysis_id)
      } else {
        console.error('Upload failed:', data.error)
      }
    } catch (error) {
      console.error('Upload error:', error)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Sports Video Analysis</h2>
      
      <div className="flex-1 flex flex-col space-y-6">
        {/* File Drop Zone / Video Preview */}
        {!file ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            className={`
              flex-1 border-2 border-dashed rounded-lg cursor-pointer transition-all duration-300
              flex flex-col items-center justify-center p-8
              ${isDragging
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100'
              }
            `}
          >
            <div className="text-center">
              <div className="mb-4 flex justify-center">
                <div className="p-4 bg-blue-100 rounded-full">
                  <Upload className="w-12 h-12 text-blue-600" />
                </div>
              </div>
              <h3 className="text-xl font-semibold mb-2 text-gray-800">
                Drag and drop a video or click to browse
              </h3>
              <p className="text-gray-600 mb-4">
                Upload your sports footage for instant analysis
              </p>
              <p className="text-sm text-gray-500">
                Supported: MP4, AVI, MOV, MKV • Max: 200MB
              </p>
            </div>
          </div>
        ) : (
          <div className="flex-1 border-2 border-gray-300 rounded-lg overflow-hidden bg-black flex flex-col">
            {videoPreviewUrl && (
              <video
                src={videoPreviewUrl}
                controls
                className="w-full h-full object-contain"
              />
            )}
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".mp4,.avi,.mov,.mkv,.webm"
          onChange={handleFileInputChange}
          className="hidden"
        />

        {/* Action Buttons */}
        {file && (
          <div className="space-y-3">
            <Button
              onClick={handleUpload}
              disabled={isUploading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              size="lg"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Analyzing Video...
                </>
              ) : (
                <>
                  <Video className="w-4 h-4 mr-2" />
                  Analyze Video
                </>
              )}
            </Button>

            <Button
              onClick={handleNewVideo}
              disabled={isUploading}
              variant="outline"
              className="w-full"
              size="lg"
            >
              <Upload className="w-4 h-4 mr-2" />
              Upload New Video
            </Button>
          </div>
        )}

        {isUploading && (
          <div className="flex items-center justify-center space-x-2 text-gray-600">
            <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
            <span className="text-sm">Processing video...</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default VideoInput