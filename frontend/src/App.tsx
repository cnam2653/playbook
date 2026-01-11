import { useState } from 'react'
import DemoVideos from './components/DemoVideos'
import VideoInput from './components/VideoInput'
import AIAnalysis from './components/AIAnalysis'

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [analysisId, setAnalysisId] = useState<string | null>(null)

  const scrollToAnalysis = () => {
    document.getElementById('analysis-section')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Hero Section */}
      <div className="h-screen flex items-center justify-center bg-slate-900">
        <div className="text-center animate-fadeIn">
          {/* Icon */}
          <div className="text-6xl mb-6">🧠</div>

          {/* Title */}
          <h1 className="text-6xl font-bold text-white mb-4">
            Sports Analytics Platform
          </h1>

          {/* Subtitle */}
          <p className="text-gray-300 text-lg mb-8 max-w-2xl mx-auto">
            Transform your game footage into professional insights with AI-powered video analysis
          </p>

          {/* Get Started Button */}
          <button
            onClick={scrollToAnalysis}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-lg transition-colors duration-200 inline-flex items-center gap-2"
          >
            Get Started
            <span>→</span>
          </button>
        </div>
      </div>

      {/* Analysis Section */}
      <div id="analysis-section" className="grid grid-cols-3 gap-6 p-6 min-h-screen">
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