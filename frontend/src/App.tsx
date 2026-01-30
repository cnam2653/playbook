import { useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, ChevronDown, Linkedin, Github, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import DemoVideos from './components/DemoVideos'
import VideoInput from './components/VideoInput'
import AIAnalysis from './components/AIAnalysis'

function App() {
  const [, setSelectedFile] = useState<File | null>(null)
  const [analysisId, setAnalysisId] = useState<string | null>(null)

  const scrollToAnalysis = () => {
    document.getElementById('analysis-section')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Hero Section */}
      <div className="h-screen flex items-center justify-center relative overflow-hidden noise-overlay">
        {/* Grid background */}
        <div className="absolute inset-0 grid-pattern" />

        {/* Stadium light glow from top */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[200%] h-[60%] pointer-events-none">
          <motion.div
            className="w-full h-full"
            animate={{
              background: [
                'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(200, 255, 0, 0.12) 0%, transparent 60%)',
                'radial-gradient(ellipse 90% 60% at 50% 0%, rgba(200, 255, 0, 0.18) 0%, transparent 60%)',
                'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(200, 255, 0, 0.12) 0%, transparent 60%)',
              ],
            }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>

        {/* Floating accent orbs */}
        <motion.div
          className="absolute top-1/4 left-1/4 w-64 h-64 rounded-full blur-[120px] pointer-events-none"
          animate={{
            background: [
              'rgba(200, 255, 0, 0.1)',
              'rgba(0, 255, 136, 0.1)',
              'rgba(200, 255, 0, 0.1)',
            ],
            x: [0, 50, 0],
            y: [0, -30, 0],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute bottom-1/3 right-1/4 w-96 h-96 rounded-full blur-[150px] pointer-events-none"
          animate={{
            background: [
              'rgba(0, 255, 136, 0.08)',
              'rgba(200, 255, 0, 0.08)',
              'rgba(0, 255, 136, 0.08)',
            ],
            x: [0, -40, 0],
            y: [0, 40, 0],
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Navigation - Top right */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="absolute top-6 right-6 z-50 flex items-center gap-4"
        >
          <span className="text-xs font-medium tracking-widest uppercase text-zinc-500 hidden md:block">
            Connect
          </span>
          <div className="flex items-center gap-2">
            <a
              href="https://www.linkedin.com/in/chrisnam28/"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative p-2.5 rounded-lg bg-zinc-900/80 border border-zinc-800 hover:border-[#c8ff00]/50 transition-all duration-300"
            >
              <Linkedin className="w-4 h-4 text-zinc-400 group-hover:text-[#c8ff00] transition-colors" />
              <div className="absolute inset-0 rounded-lg bg-[#c8ff00]/0 group-hover:bg-[#c8ff00]/5 transition-colors" />
            </a>
            <a
              href="https://github.com/cnam2653"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative p-2.5 rounded-lg bg-zinc-900/80 border border-zinc-800 hover:border-[#c8ff00]/50 transition-all duration-300"
            >
              <Github className="w-4 h-4 text-zinc-400 group-hover:text-[#c8ff00] transition-colors" />
              <div className="absolute inset-0 rounded-lg bg-[#c8ff00]/0 group-hover:bg-[#c8ff00]/5 transition-colors" />
            </a>
          </div>
        </motion.div>

        {/* Main Hero Content */}
        <div className="text-center z-10 px-4 max-w-5xl mx-auto">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-8 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-900/60 border border-zinc-800 backdrop-blur-sm"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#c8ff00] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#c8ff00]"></span>
            </span>
            <span className="text-xs font-medium tracking-wider uppercase text-zinc-400">
              AI-Powered Analysis
            </span>
          </motion.div>

          {/* Main Title */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.15 }}
            className="mb-6"
          >
            <h1 className="font-display text-6xl md:text-8xl lg:text-9xl tracking-tight text-white leading-[0.85]">
              PLAYBOOK
            </h1>
            <div className="flex items-center justify-center gap-4 mt-4">
              <div className="h-[1px] w-16 bg-gradient-to-r from-transparent to-[#c8ff00]/50" />
              <Activity className="w-5 h-5 text-[#c8ff00]" />
              <div className="h-[1px] w-16 bg-gradient-to-l from-transparent to-[#c8ff00]/50" />
            </div>
          </motion.div>

          {/* Tagline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-lg md:text-xl text-zinc-400 mb-4 font-light tracking-wide"
          >
            Sports Analytics Platform
          </motion.p>

          {/* Slogan */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-2xl md:text-3xl font-light mb-12 text-[#c8ff00]"
          >
            Transform your game, one frame at a time
          </motion.p>

          {/* CTA Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.55 }}
            className="flex flex-col items-center gap-6"
          >
            <Button
              onClick={scrollToAnalysis}
              size="lg"
              className="group relative px-8 py-6 text-base font-semibold tracking-wider uppercase bg-[#c8ff00] text-black hover:bg-[#d4ff33] rounded-lg overflow-hidden transition-all duration-300 hover:shadow-[0_0_40px_rgba(200,255,0,0.3)]"
            >
              <span className="relative z-10 flex items-center gap-3">
                <Zap className="w-4 h-4" />
                Start Analysis
              </span>
            </Button>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.6 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        >
          <span className="text-[10px] font-medium tracking-[0.2em] uppercase text-zinc-600">
            Scroll
          </span>
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          >
            <ChevronDown className="w-5 h-5 text-zinc-600" />
          </motion.div>
        </motion.div>
      </div>

      {/* Analysis Section */}
      <div id="analysis-section" className="min-h-screen py-20 px-6 relative">
        {/* Section background effects */}
        <div className="absolute inset-0 grid-pattern opacity-50" />
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#c8ff00]/20 to-transparent" />

        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="max-w-7xl mx-auto mb-16 text-center relative z-10"
        >
          <div className="inline-flex items-center gap-3 mb-6">
            <div className="h-[1px] w-12 bg-gradient-to-r from-transparent to-[#c8ff00]/50" />
            <span className="text-xs font-medium tracking-[0.25em] uppercase text-[#c8ff00]">
              Analysis Suite
            </span>
            <div className="h-[1px] w-12 bg-gradient-to-l from-transparent to-[#c8ff00]/50" />
          </div>
          <h2 className="font-display text-4xl md:text-6xl text-white mb-4 tracking-tight">
            PROFESSIONAL SPORTS ANALYSIS
          </h2>
          <p className="text-zinc-500 text-lg max-w-2xl mx-auto">
            Upload your footage, leverage AI-powered insights, and elevate your performance with data-driven analysis
          </p>
        </motion.div>

        {/* Three Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto relative z-10">
          {/* Demo Videos Card */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            viewport={{ once: true }}
            className="glass-card rounded-2xl overflow-hidden transition-all duration-500"
          >
            <div className="p-6 border-b border-zinc-800/50">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-lg bg-[#c8ff00]/10 flex items-center justify-center">
                  <span className="text-[#c8ff00] text-sm font-display">01</span>
                </div>
                <h3 className="font-display text-xl tracking-wide text-white">DEMO VIDEOS</h3>
              </div>
              <p className="text-sm text-zinc-500">Explore sample analysis workflows</p>
            </div>
            <div className="p-6">
              <DemoVideos onSelectDemo={(videoUrl: string) => console.log('Selected demo:', videoUrl)} />
            </div>
          </motion.div>

          {/* Video Upload Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            viewport={{ once: true }}
            className="glass-card rounded-2xl overflow-hidden transition-all duration-500"
          >
            <div className="p-6 border-b border-zinc-800/50">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-lg bg-[#c8ff00]/10 flex items-center justify-center">
                  <span className="text-[#c8ff00] text-sm font-display">02</span>
                </div>
                <h3 className="font-display text-xl tracking-wide text-white">UPLOAD VIDEO</h3>
              </div>
              <p className="text-sm text-zinc-500">Drag & drop your sports footage</p>
            </div>
            <div className="p-6">
              <VideoInput
                onFileSelect={setSelectedFile}
                onAnalysisStart={setAnalysisId}
              />
            </div>
          </motion.div>

          {/* AI Analysis Card */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            viewport={{ once: true }}
            className="glass-card rounded-2xl overflow-hidden transition-all duration-500"
          >
            <div className="p-6 border-b border-zinc-800/50">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-lg bg-[#c8ff00]/10 flex items-center justify-center">
                  <span className="text-[#c8ff00] text-sm font-display">03</span>
                </div>
                <h3 className="font-display text-xl tracking-wide text-white">AI ANALYSIS</h3>
              </div>
              <p className="text-sm text-zinc-500">Real-time machine learning insights</p>
            </div>
            <div className="p-6">
              <AIAnalysis analysisId={analysisId} />
            </div>
          </motion.div>
        </div>

        {/* Bottom accent line */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-zinc-800 to-transparent" />
      </div>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-zinc-900">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Activity className="w-4 h-4 text-[#c8ff00]" />
            <span className="font-display text-lg tracking-wider text-zinc-400">PLAYBOOK</span>
          </div>
          <p className="text-xs text-zinc-600">
            Built with AI-powered sports analytics technology
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
