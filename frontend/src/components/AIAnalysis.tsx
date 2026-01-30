import { useState, useEffect } from 'react'
import { Bot, Sparkles, Zap, Loader2, Send, MessageSquare, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { motion, AnimatePresence } from 'framer-motion'

interface AIAnalysisProps {
  analysisId: string | null
}

const AIAnalysis: React.FC<AIAnalysisProps> = ({ analysisId }) => {
  const [analysis, setAnalysis] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [query, setQuery] = useState('')
  const [queryResponse, setQueryResponse] = useState('')
  const [isQuerying, setIsQuerying] = useState(false)
  const [activeQuestion, setActiveQuestion] = useState<string | null>(null)

  const quickQuestions: string[] = [
    "Who had the most possession?",
    "Which player was fastest?",
    "What formation is being used?",
    "How many passes completed?",
    "Most active pitch areas?",
    "Average player speed?"
  ]

  useEffect(() => {
    if (analysisId) {
      fetchAnalysis()
    }
  }, [analysisId])

  const fetchAnalysis = async () => {
    if (!analysisId) return

    setIsLoading(true)
    try {
      const response = await fetch(`http://localhost:5001/api/analysis/${analysisId}/summary`)
      const data = await response.json()

      if (response.ok) {
        setAnalysis(data.summary)
      }
    } catch (error) {
      console.error('Error fetching analysis:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuery = async (question: string = query) => {
    if (!analysisId || (!question && !query)) return

    setIsQuerying(true)
    setQueryResponse('')
    setActiveQuestion(question || query)

    try {
      const response = await fetch(`http://localhost:5001/api/analysis/${analysisId}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: question || query })
      })

      const data = await response.json()

      if (response.ok) {
        setQueryResponse(data.response)
      }
    } catch (error) {
      console.error('Error querying analysis:', error)
      setQueryResponse('Error getting response. Please try again.')
    } finally {
      setIsQuerying(false)
    }
  }

  const handleQuickQuestion = (question: string) => {
    setQuery(question)
    handleQuery(question)
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleQuery()
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 flex flex-col space-y-4 overflow-hidden">
        <AnimatePresence mode="wait">
          {!analysisId ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex items-center justify-center"
            >
              <div className="text-center px-4">
                {/* Bot icon with glow effect */}
                <div className="mb-6 inline-block">
                  <div className="relative">
                    <div className="absolute inset-0 bg-[#c8ff00]/20 rounded-full blur-xl animate-pulse" />
                    <div className="relative w-20 h-20 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center">
                      <Bot className="w-10 h-10 text-zinc-500" />
                    </div>
                  </div>
                </div>

                <h3 className="text-sm font-medium text-zinc-400 mb-2">
                  AI Assistant Ready
                </h3>
                <p className="text-xs text-zinc-600 max-w-[200px] mx-auto">
                  Upload a video to unlock AI-powered insights and real-time analysis
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="analysis"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex-1 flex flex-col space-y-4 overflow-hidden"
            >
              {/* AI Summary Section */}
              {isLoading ? (
                <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#c8ff00]/10 flex items-center justify-center">
                      <Loader2 className="w-4 h-4 text-[#c8ff00] animate-spin" />
                    </div>
                    <div className="flex-1">
                      <div className="h-2 bg-zinc-800 rounded animate-pulse w-3/4 mb-2" />
                      <div className="h-2 bg-zinc-800 rounded animate-pulse w-1/2" />
                    </div>
                  </div>
                </div>
              ) : analysis && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 rounded-xl bg-gradient-to-br from-[#c8ff00]/10 to-transparent border border-[#c8ff00]/20"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#c8ff00]/20 flex items-center justify-center flex-shrink-0">
                      <Sparkles className="w-4 h-4 text-[#c8ff00]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-xs font-semibold text-[#c8ff00] uppercase tracking-wider mb-2">
                        AI Summary
                      </h3>
                      <p className="text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed">
                        {analysis}
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Quick Questions */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 px-1">
                  <Zap className="w-3 h-3 text-[#c8ff00]" />
                  <span className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider">
                    Quick Questions
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto">
                  {quickQuestions.map((question, index) => (
                    <motion.button
                      key={index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      onClick={() => handleQuickQuestion(question)}
                      disabled={isQuerying}
                      className={`
                        group text-left p-2.5 text-[11px] rounded-lg transition-all duration-200
                        ${activeQuestion === question && isQuerying
                          ? 'bg-[#c8ff00]/10 border border-[#c8ff00]/30 text-[#c8ff00]'
                          : 'bg-zinc-900/50 border border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200 hover:bg-zinc-800/50'
                        }
                      `}
                    >
                      <span className="flex items-center gap-1.5">
                        <ChevronRight className={`w-3 h-3 transition-transform ${activeQuestion === question ? 'rotate-90 text-[#c8ff00]' : 'group-hover:translate-x-0.5'}`} />
                        {question}
                      </span>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Custom Query Input */}
              <div className="space-y-3">
                <div className="relative">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask anything about the clip..."
                    className="w-full px-4 py-3 pr-12 rounded-xl bg-zinc-900/70 border border-zinc-800 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-[#c8ff00]/50 focus:ring-1 focus:ring-[#c8ff00]/20 transition-all"
                  />
                  <button
                    onClick={() => handleQuery()}
                    disabled={!query || isQuerying}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-[#c8ff00] text-black hover:bg-[#d4ff33] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                  >
                    {isQuerying ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Query Response */}
              <AnimatePresence>
                {(queryResponse || isQuerying) && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, height: 0 }}
                    animate={{ opacity: 1, y: 0, height: 'auto' }}
                    exit={{ opacity: 0, y: -10, height: 0 }}
                    className="flex-1 min-h-[100px] overflow-hidden"
                  >
                    <div className="h-full p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
                      <div className="flex items-start gap-3">
                        <div className="w-6 h-6 rounded-md bg-zinc-800 flex items-center justify-center flex-shrink-0">
                          <MessageSquare className="w-3 h-3 text-zinc-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          {isQuerying ? (
                            <div className="flex items-center gap-2 text-sm text-zinc-400">
                              <span className="inline-flex gap-1">
                                <span className="w-1.5 h-1.5 bg-[#c8ff00] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                <span className="w-1.5 h-1.5 bg-[#c8ff00] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                <span className="w-1.5 h-1.5 bg-[#c8ff00] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                              </span>
                              Analyzing...
                            </div>
                          ) : (
                            <p className="text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed">
                              {queryResponse}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default AIAnalysis
