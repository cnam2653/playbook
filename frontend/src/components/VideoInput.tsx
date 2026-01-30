import { useState, useRef } from 'react'
import { Upload, Video, Loader2, CloudUpload, X, Sparkles, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { motion, AnimatePresence } from 'framer-motion'

interface VideoInputProps {
  onFileSelect: (file: File | null) => void
  onAnalysisStart: (analysisId: string) => void
}

const VideoInput: React.FC<VideoInputProps> = ({ onFileSelect, onAnalysisStart }) => {
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null)
  const [analyzedVideoUrl, setAnalyzedVideoUrl] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile)
    onFileSelect(selectedFile)
    const previewUrl = URL.createObjectURL(selectedFile)
    setVideoPreviewUrl(previewUrl)
    setAnalyzedVideoUrl(null) // Reset analyzed video when new file selected
  }

  const handleNewVideo = () => {
    setFile(null)
    setVideoPreviewUrl(null)
    setAnalyzedVideoUrl(null)
    onFileSelect(null)
    setUploadProgress(0)
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
    setUploadProgress(0)

    // Simulate progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return prev
        }
        return prev + Math.random() * 15
      })
    }, 200)

    const formData = new FormData()
    formData.append('video', file)
    formData.append('sport', 'soccer')

    try {
      const response = await fetch('http://localhost:5001/upload', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (response.ok) {
        setUploadProgress(100)
        onAnalysisStart(data.analysis_id)

        // Set the analyzed video URL
        if (data.output_video) {
          setAnalyzedVideoUrl(`http://localhost:5001/outputs/${data.output_video}`)
        }
      } else {
        console.error('Upload failed:', data.error)
      }
    } catch (error) {
      console.error('Upload error:', error)
    } finally {
      clearInterval(progressInterval)
      setIsUploading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 flex flex-col space-y-4">
        <AnimatePresence mode="wait">
          {!file ? (
            <motion.div
              key="dropzone"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`
                relative flex-1 min-h-[280px] rounded-xl cursor-pointer transition-all duration-300 overflow-hidden
                ${isDragging
                  ? 'border-2 border-[#c8ff00] bg-[#c8ff00]/5'
                  : 'border-2 border-dashed border-zinc-700 hover:border-zinc-500 bg-zinc-900/30 hover:bg-zinc-900/50'
                }
              `}
            >
              {/* Background grid pattern */}
              <div
                className="absolute inset-0 opacity-30"
                style={{
                  backgroundImage: `
                    linear-gradient(rgba(200, 255, 0, 0.05) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(200, 255, 0, 0.05) 1px, transparent 1px)
                  `,
                  backgroundSize: '30px 30px'
                }}
              />

              <div className="relative flex flex-col items-center justify-center h-full p-6 text-center">
                {/* Upload Icon with animation */}
                <motion.div
                  animate={isDragging ? { scale: 1.1, y: -5 } : { scale: 1, y: 0 }}
                  className="mb-4"
                >
                  <div className={`
                    w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300
                    ${isDragging
                      ? 'bg-[#c8ff00]/20 text-[#c8ff00]'
                      : 'bg-zinc-800 text-zinc-400'
                    }
                  `}>
                    <CloudUpload className="w-8 h-8" />
                  </div>
                </motion.div>

                <h3 className={`
                  text-base font-semibold mb-2 transition-colors
                  ${isDragging ? 'text-[#c8ff00]' : 'text-zinc-200'}
                `}>
                  {isDragging ? 'Drop your video here' : 'Drag & drop video'}
                </h3>

                <p className="text-sm text-zinc-500 mb-4">
                  or click to browse files
                </p>

                <div className="flex items-center gap-3 text-[10px] text-zinc-600 uppercase tracking-wider">
                  <span className="px-2 py-1 rounded bg-zinc-800/50">MP4</span>
                  <span className="px-2 py-1 rounded bg-zinc-800/50">AVI</span>
                  <span className="px-2 py-1 rounded bg-zinc-800/50">MOV</span>
                  <span className="px-2 py-1 rounded bg-zinc-800/50">MKV</span>
                </div>

                <p className="text-[10px] text-zinc-600 mt-3">
                  Maximum file size: 200MB
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex-1 flex flex-col"
            >
              {/* Original Video Preview */}
              <div className="relative rounded-xl overflow-hidden bg-black border border-zinc-800 h-40">
                {videoPreviewUrl && (
                  <video
                    src={videoPreviewUrl}
                    controls
                    className="w-full h-full object-contain"
                  />
                )}

                {/* Remove button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleNewVideo()
                  }}
                  className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 backdrop-blur-sm text-zinc-400 hover:text-white hover:bg-black/80 transition-all"
                >
                  <X className="w-3 h-3" />
                </button>

                {/* File info overlay */}
                <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/80 to-transparent">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Video className="w-3 h-3 text-zinc-400" />
                      <span className="text-[10px] text-zinc-300 truncate max-w-[120px]">
                        {file.name}
                      </span>
                    </div>
                    <span className="text-[9px] text-zinc-500">
                      {formatFileSize(file.size)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Analyzed Video Output */}
              {analyzedVideoUrl && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-3"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="w-3 h-3 text-[#c8ff00]" />
                    <span className="text-[10px] font-medium text-[#c8ff00] uppercase tracking-wider">
                      Analyzed Output
                    </span>
                  </div>
                  <div className="relative rounded-xl overflow-hidden bg-black border border-[#c8ff00]/30 h-40">
                    <video
                      src={analyzedVideoUrl}
                      controls
                      className="w-full h-full object-contain"
                    />
                    {/* Glow effect */}
                    <div className="absolute inset-0 pointer-events-none border border-[#c8ff00]/20 rounded-xl" />
                  </div>
                </motion.div>
              )}

              {/* Progress bar */}
              {isUploading && (
                <div className="mt-3">
                  <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                      className="h-full bg-gradient-to-r from-[#c8ff00] to-[#00ff88]"
                    />
                  </div>
                  <p className="text-[10px] text-zinc-500 mt-1 text-center">
                    Processing video... {Math.round(uploadProgress)}%
                  </p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        <input
          ref={fileInputRef}
          type="file"
          accept=".mp4,.avi,.mov,.mkv,.webm"
          onChange={handleFileInputChange}
          className="hidden"
        />

        {/* Action Buttons */}
        {file && !analyzedVideoUrl && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-2"
          >
            <Button
              onClick={handleUpload}
              disabled={isUploading}
              variant="electric"
              size="lg"
              className="w-full"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing Video...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Analyze Video
                </>
              )}
            </Button>
          </motion.div>
        )}

        {/* Upload new video button after analysis */}
        {analyzedVideoUrl && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Button
              onClick={handleNewVideo}
              variant="outline"
              size="sm"
              className="w-full"
            >
              <Upload className="w-3 h-3" />
              Upload New Video
            </Button>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default VideoInput
