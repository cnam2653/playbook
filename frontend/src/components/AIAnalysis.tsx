import { useState, useEffect } from 'react'
import { Bot, Sparkles, Zap, Loader2, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface AIAnalysisProps {
  analysisId: string | null
}

const AIAnalysis: React.FC<AIAnalysisProps> = ({ analysisId }) => {
  const [analysis, setAnalysis] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [query, setQuery] = useState('')
  const [queryResponse, setQueryResponse] = useState('')
  const [isQuerying, setIsQuerying] = useState(false)

  const quickQuestions: string[] = [
    "What player had the most possession in this clip?",
    "Which player was the fastest?", 
    "What tactical formation is being used?",
    "How many passes were completed?",
    "Which areas of the pitch had most activity?",
    "What was the average speed of player movements?"
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
      const response = await fetch(`http://localhost:5000/api/analysis/${analysisId}/summary`)
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

    try {
      const response = await fetch(`http://localhost:5000/api/analysis/${analysisId}/query`, {
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
      <h2 className="text-2xl font-bold mb-6 text-gray-800">AI Analysis/Chatbot or something</h2>
      
      <div className="flex-1 flex flex-col space-y-6 overflow-hidden">
        {!analysisId ? (
          <div className="flex-1 flex items-center justify-center text-gray-500 text-center">
            <div>
              <div className="mb-4 flex justify-center">
                <div className="p-4 bg-purple-100 rounded-full">
                  <Bot className="w-12 h-12 text-purple-600" />
                </div>
              </div>
              <p>Upload a video to get AI-powered insights and ask questions about your sports footage.</p>
            </div>
          </div>
        ) : (
          <>
            {/* AI Summary */}
            {isLoading ? (
              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span className="text-sm text-blue-700">Generating AI summary...</span>
                </div>
              </div>
            ) : analysis && (
              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <h3 className="text-lg font-semibold text-blue-800 mb-2 flex items-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  AI Analysis Summary
                </h3>
                <div className="text-blue-700 whitespace-pre-wrap text-sm">
                  {analysis}
                </div>
              </div>
            )}

            {/* Quick Questions */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-3 text-gray-800 flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-600" />
                Quick Analysis
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {quickQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickQuestion(question)}
                    className="w-full text-left p-2 text-sm bg-white border border-gray-300 rounded hover:border-blue-500 hover:bg-blue-50 transition-colors"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Query */}
            <div className="flex-1 flex flex-col space-y-4">
              <div>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask anything about the clip..."
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
                <Button
                  onClick={() => handleQuery()}
                  disabled={!query || isQuerying}
                  className="w-full mt-2 bg-green-600 hover:bg-green-700"
                  size="default"
                >
                  {isQuerying ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      Ask Question
                    </>
                  )}
                </Button>
              </div>

              {/* Query Response */}
              {(queryResponse || isQuerying) && (
                <div className="flex-1 bg-gray-50 border-l-4 border-blue-600 p-4 rounded overflow-y-auto">
                  <strong className="text-gray-800">Answer:</strong>
                  <div className="mt-2 text-sm text-gray-700">
                    {isQuerying ? (
                      <div className="flex items-center space-x-2">
                        <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                        <span>Analyzing...</span>
                      </div>
                    ) : (
                      <div className="whitespace-pre-wrap">{queryResponse}</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default AIAnalysis