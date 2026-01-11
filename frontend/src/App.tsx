import { useState } from 'react'
import { motion } from 'framer-motion'
import { Brain, ArrowDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="h-screen flex items-center justify-center bg-slate-900 relative overflow-hidden">
        {/* Animated background gradient */}
        <motion.div
          className="absolute inset-0 opacity-30"
          animate={{
            background: [
              'radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.5) 0%, transparent 50%)',
              'radial-gradient(circle at 80% 50%, rgba(147, 51, 234, 0.5) 0%, transparent 50%)',
              'radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.5) 0%, transparent 50%)',
            ],
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
        />

        <div className="text-center z-10 px-4">
          {/* Icon with animation */}
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="mb-6 inline-block"
          >
            <Brain className="w-16 h-16 text-blue-400 mx-auto" />
          </motion.div>

          {/* Title with staggered animation */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-4"
          >
            Sports Analytics Platform
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-gray-300 text-lg md:text-xl mb-8 max-w-2xl mx-auto"
          >
            Transform your game footage into professional insights with AI-powered video analysis
          </motion.p>

          {/* Get Started Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <Button
              onClick={scrollToAnalysis}
              size="lg"
              className="text-base font-semibold"
            >
              Get Started
              <ArrowDown className="ml-2 h-4 w-4" />
            </Button>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, y: [0, 10, 0] }}
            transition={{
              opacity: { delay: 1.2, duration: 0.6 },
              y: { delay: 1.8, duration: 1.5, repeat: Infinity }
            }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2"
          >
            <ArrowDown className="w-6 h-6 text-gray-400" />
          </motion.div>
        </div>
      </div>

      {/* Analysis Section */}
      <div id="analysis-section" className="min-h-screen py-16 px-6">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="max-w-7xl mx-auto mb-12 text-center"
        >
          <h2 className="text-4xl font-bold mb-4">Professional Sports Analysis</h2>
          <p className="text-gray-600 text-lg">
            Upload your videos, get insights, and improve performance with our AI-powered platform
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl mx-auto">
          {/* Left Column - Demo Videos */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            viewport={{ once: true }}
          >
            <Card className="h-full hover:shadow-xl transition-shadow duration-300">
              <CardHeader>
                <CardTitle>Demo Videos</CardTitle>
                <CardDescription>Try our sample analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <DemoVideos onSelectDemo={(videoUrl: string) => console.log('Selected demo:', videoUrl)} />
              </CardContent>
            </Card>
          </motion.div>

          {/* Middle Column - Video Input */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            viewport={{ once: true }}
          >
            <Card className="h-full hover:shadow-xl transition-shadow duration-300">
              <CardHeader>
                <CardTitle>Upload Video</CardTitle>
                <CardDescription>Upload a video to get AI-powered insights</CardDescription>
              </CardHeader>
              <CardContent>
                <VideoInput
                  onFileSelect={setSelectedFile}
                  onAnalysisStart={setAnalysisId}
                />
              </CardContent>
            </Card>
          </motion.div>

          {/* Right Column - AI Analysis */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            viewport={{ once: true }}
          >
            <Card className="h-full hover:shadow-xl transition-shadow duration-300">
              <CardHeader>
                <CardTitle>AI Analysis</CardTitle>
                <CardDescription>Real-time insights from machine learning</CardDescription>
              </CardHeader>
              <CardContent>
                <AIAnalysis analysisId={analysisId} />
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  )
}

export default App