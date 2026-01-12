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
  const [sport, setSport] = useState('soccer')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile)
    onFileSelect(selectedFile)
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
    formData.append('sport', sport)

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
        {/* File Drop Zone */}
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
            {file && (
              <div className="mt-4 p-2 bg-white rounded border">
                <p className="text-sm font-medium text-green-600">
                  Selected: {file.name}
                </p>
              </div>
            )}
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".mp4,.avi,.mov,.mkv,.webm"
          onChange={handleFileInputChange}
          className="hidden"
        />

        {/* Sport Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Sport Type
          </label>
          <select
            value={sport}
            onChange={(e) => setSport(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="soccer">Soccer / Football</option>
            <option value="basketball">Basketball</option>
            <option value="american_football">American Football</option>
            <option value="rugby">Rugby</option>
            <option value="hockey">Hockey</option>
          </select>
        </div>

        {/* Upload Button */}
        <Button
          onClick={handleUpload}
          disabled={!file || isUploading}
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