import { useState } from 'react'
import { Play, Film, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { motion, AnimatePresence } from 'framer-motion'

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
  const [playingVideo, setPlayingVideo] = useState<string | null>(null)

  const demoVideos: DemoVideo[] = [
    {
      id: 1,
      title: "Soccer Match Demo",
      description: "Full match analysis with player tracking",
      thumbnail: "/api/placeholder/300/200",
      url: "/demo.mp4",
      duration: "0:14"
    }
  ]

  const handlePlayDemo = (video: DemoVideo) => {
    setSelectedDemo(video.id)
    setPlayingVideo(video.url)
    onSelectDemo(video.url)
  }

  const handleCloseVideo = () => {
    setPlayingVideo(null)
    setSelectedDemo(null)
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 space-y-4">
        <AnimatePresence mode="wait">
          {playingVideo ? (
            <motion.div
              key="video-player"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative"
            >
              {/* Video Player */}
              <div className="relative rounded-xl overflow-hidden bg-black border border-[#c8ff00]/30">
                <video
                  src={playingVideo}
                  controls
                  autoPlay
                  className="w-full h-auto max-h-[300px] object-contain"
                />

                {/* Close button */}
                <button
                  onClick={handleCloseVideo}
                  className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 backdrop-blur-sm text-zinc-400 hover:text-white hover:bg-black/80 transition-all z-10"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Video info */}
              <div className="mt-3 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-sm text-[#c8ff00]">
                    {demoVideos.find(v => v.url === playingVideo)?.title}
                  </h3>
                  <p className="text-xs text-zinc-500">Now playing</p>
                </div>
                <Button
                  onClick={handleCloseVideo}
                  variant="outline"
                  size="sm"
                >
                  Close
                </Button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="video-list"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {demoVideos.map((video, index) => (
                <motion.div
                  key={video.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="group relative p-4 rounded-xl cursor-pointer transition-all duration-300 bg-zinc-900/50 border border-zinc-800/50 hover:border-zinc-700 hover:bg-zinc-800/30"
                >
                  {/* Video Preview Thumbnail */}
                  <div
                    onClick={() => handlePlayDemo(video)}
                    className="relative w-full h-28 rounded-lg overflow-hidden mb-3 bg-zinc-900"
                  >
                    {/* Video thumbnail preview */}
                    <video
                      src={video.url}
                      className="absolute inset-0 w-full h-full object-cover"
                      muted
                      preload="metadata"
                    />

                    {/* Overlay gradient */}
                    <div className="absolute inset-0 bg-black/30 group-hover:bg-black/20 transition-all" />

                    {/* Play button overlay */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 bg-zinc-800/80 text-zinc-400 group-hover:bg-[#c8ff00] group-hover:text-black">
                        <Play className="w-5 h-5 ml-0.5" fill="currentColor" />
                      </div>
                    </div>

                    {/* Duration badge */}
                    <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-medium text-zinc-300 backdrop-blur-sm">
                      {video.duration}
                    </div>

                    {/* Film icon */}
                    <div className="absolute top-2 left-2">
                      <Film className="w-4 h-4 text-zinc-400" />
                    </div>
                  </div>

                  {/* Video Info */}
                  <div className="space-y-1">
                    <h3 className="font-semibold text-sm tracking-wide transition-colors text-zinc-200 group-hover:text-white">
                      {video.title}
                    </h3>
                    <p className="text-xs text-zinc-500">{video.description}</p>
                  </div>

                  {/* Play Demo Button */}
                  <Button
                    onClick={() => handlePlayDemo(video)}
                    variant="outline"
                    size="sm"
                    className="w-full mt-3 group-hover:bg-[#c8ff00]/10 group-hover:border-[#c8ff00]/50 group-hover:text-[#c8ff00]"
                  >
                    <Play className="w-3 h-3" />
                    Play Demo
                  </Button>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default DemoVideos
