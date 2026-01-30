import { useState } from 'react'
import { Play, Film } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { motion } from 'framer-motion'

interface DemoVideo {
  id: number
  title: string
  description: string
  thumbnail: string
  url: string
  duration: string
}

interface DemoVideosProps {
  onSelectDemo: (videoUrl: string) => void
}

const DemoVideos: React.FC<DemoVideosProps> = ({ onSelectDemo }) => {
  const [selectedDemo, setSelectedDemo] = useState<number | null>(null)
  const [hoveredDemo, setHoveredDemo] = useState<number | null>(null)

  const demoVideos: DemoVideo[] = [
    {
      id: 1,
      title: "Match Analysis",
      description: "Full soccer match tactical breakdown",
      thumbnail: "/api/placeholder/300/200",
      url: "/demo-video-1.mp4",
      duration: "2:34"
    },
    {
      id: 2,
      title: "Player Tracking",
      description: "Advanced movement & speed analysis",
      thumbnail: "/api/placeholder/300/200",
      url: "/demo-video-2.mp4",
      duration: "1:45"
    }
  ]

  const handleSelectDemo = (video: DemoVideo) => {
    setSelectedDemo(video.id)
    onSelectDemo(video.url)
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 space-y-4">
        {demoVideos.map((video, index) => (
          <motion.div
            key={video.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => handleSelectDemo(video)}
            onMouseEnter={() => setHoveredDemo(video.id)}
            onMouseLeave={() => setHoveredDemo(null)}
            className={`
              group relative p-4 rounded-xl cursor-pointer transition-all duration-300
              ${selectedDemo === video.id
                ? 'bg-[#c8ff00]/10 border border-[#c8ff00]/30'
                : 'bg-zinc-900/50 border border-zinc-800/50 hover:border-zinc-700 hover:bg-zinc-800/30'
              }
            `}
          >
            {/* Video Preview Thumbnail */}
            <div className="relative w-full h-28 rounded-lg overflow-hidden mb-3 bg-zinc-900">
              {/* Gradient overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-zinc-800 via-zinc-900 to-black" />

              {/* Grid pattern */}
              <div
                className="absolute inset-0 opacity-20"
                style={{
                  backgroundImage: `
                    linear-gradient(rgba(200, 255, 0, 0.1) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(200, 255, 0, 0.1) 1px, transparent 1px)
                  `,
                  backgroundSize: '20px 20px'
                }}
              />

              {/* Play button overlay */}
              <div className={`
                absolute inset-0 flex items-center justify-center transition-all duration-300
                ${hoveredDemo === video.id || selectedDemo === video.id ? 'opacity-100' : 'opacity-60'}
              `}>
                <div className={`
                  w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300
                  ${selectedDemo === video.id
                    ? 'bg-[#c8ff00] text-black'
                    : 'bg-zinc-800/80 text-zinc-400 group-hover:bg-[#c8ff00]/20 group-hover:text-[#c8ff00]'
                  }
                `}>
                  <Play className="w-5 h-5 ml-0.5" fill="currentColor" />
                </div>
              </div>

              {/* Duration badge */}
              <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-medium text-zinc-300 backdrop-blur-sm">
                {video.duration}
              </div>

              {/* Film icon */}
              <div className="absolute top-2 left-2">
                <Film className="w-4 h-4 text-zinc-600" />
              </div>
            </div>

            {/* Video Info */}
            <div className="space-y-1">
              <h3 className={`
                font-semibold text-sm tracking-wide transition-colors
                ${selectedDemo === video.id ? 'text-[#c8ff00]' : 'text-zinc-200 group-hover:text-white'}
              `}>
                {video.title}
              </h3>
              <p className="text-xs text-zinc-500">{video.description}</p>
            </div>

            {/* Load Demo Button */}
            <Button
              variant={selectedDemo === video.id ? "default" : "outline"}
              size="sm"
              className="w-full mt-3"
            >
              <Play className="w-3 h-3" />
              {selectedDemo === video.id ? 'Selected' : 'Load Demo'}
            </Button>

            {/* Selection indicator */}
            {selectedDemo === video.id && (
              <motion.div
                layoutId="selection-indicator"
                className="absolute -left-px top-4 bottom-4 w-[2px] bg-[#c8ff00] rounded-full"
              />
            )}
          </motion.div>
        ))}
      </div>
    </div>
  )
}

export default DemoVideos
