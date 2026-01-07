import { useState } from 'react'
import DemoVideos from './components/DemoVideos'
import VideoInput from './components/VideoInput'
import AIAnalysis from './components/AIAnalysis'

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [analysisId, setAnalysisId] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="grid grid-cols-3 gap-6 p-6 h-screen">
        {/* Left Column - Demo Videos */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <DemoVideos onSelectDemo={(videoUrl: string) => console.log('Selected demo:', videoUrl)} />
        </div>

        {/* Middle Column - Video Input */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <VideoInput 
            onFileSelect={setSelectedFile}
            onAnalysisStart={setAnalysisId}
          />
        </div>

        {/* Right Column - AI Analysis */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <AIAnalysis analysisId={analysisId} />
        </div>
      </div>
    </div>
  )
}

export default App