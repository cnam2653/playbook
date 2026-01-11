import { useState } from 'react'
import { Play, Video } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface DemoVideo {
  id: number
  title: string
  description: string
  thumbnail: string
  url: string
}

interface DemoVideosProps {
  onSelectDemo: (videoUrl: string) => void
}

const DemoVideos: React.FC<DemoVideosProps> = ({ onSelectDemo }) => {
  const [selectedDemo, setSelectedDemo] = useState<number | null>(null)

  const demoVideos: DemoVideo[] = [
    {
      id: 1,
      title: "Input demo soccer video",
      description: "Sample soccer match analysis",
      thumbnail: "/api/placeholder/300/200",
      url: "/demo-video-1.mp4"
    },
    {
      id: 2,
      title: "Input demo soccer video 2", 
      description: "Advanced tactical analysis",
      thumbnail: "/api/placeholder/300/200",
      url: "/demo-video-2.mp4"
    }
  ]

  const handleSelectDemo = (video: DemoVideo) => {
    setSelectedDemo(video.id)
    onSelectDemo(video.url)
  }

  return (
    <div className="h-full flex flex-col">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">DEMO VIDEOS</h2>
      
      <div className="flex-1 space-y-4">
        {demoVideos.map((video) => (
          <div
            key={video.id}
            onClick={() => handleSelectDemo(video)}
            className={`
              p-4 rounded-lg border-2 cursor-pointer transition-all duration-300
              ${selectedDemo === video.id 
                ? 'border-blue-500 bg-blue-50 shadow-lg transform -translate-y-1' 
                : 'border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100'
              }
            `}
          >
            <div className="flex flex-col space-y-3">
              <div className="w-full h-32 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg flex flex-col items-center justify-center">
                <Video className="w-8 h-8 text-gray-400 mb-2" />
                <span className="text-gray-500 text-xs">Video Preview</span>
              </div>
              <h3 className="font-semibold text-lg text-gray-800">{video.title}</h3>
              <p className="text-sm text-gray-600">{video.description}</p>
              <Button className="mt-2 w-full" size="sm">
                <Play className="w-4 h-4 mr-2" />
                Load Demo
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default DemoVideos