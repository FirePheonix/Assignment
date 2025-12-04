"use client";

import React, { useState, useRef, useEffect } from 'react';
import { 
  X, 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  SkipBack, 
  SkipForward,
  Download,
  ExternalLink,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { type WorkspaceMediaItem } from '@/hooks/use-workspace-media';

interface MediaViewerProps {
  media: WorkspaceMediaItem | null;
  onClose: () => void;
  allMedia?: WorkspaceMediaItem[];
  currentIndex?: number;
  onNavigate?: (index: number) => void;
}

export function MediaViewer({ 
  media, 
  onClose, 
  allMedia = [], 
  currentIndex = 0,
  onNavigate 
}: MediaViewerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [imageError, setImageError] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!media) return;
      
      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowLeft':
          if (allMedia.length > 1 && currentIndex > 0) {
            onNavigate?.(currentIndex - 1);
          }
          break;
        case 'ArrowRight':
          if (allMedia.length > 1 && currentIndex < allMedia.length - 1) {
            onNavigate?.(currentIndex + 1);
          }
          break;
        case ' ':
          e.preventDefault();
          if (media.mediaType === 'video' && videoRef.current) {
            togglePlay();
          }
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [media, currentIndex, allMedia.length, onNavigate, onClose]);

  useEffect(() => {
    // Reset states when media changes
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setImageError(false);
  }, [media]);

  const togglePlay = () => {
    if (media?.mediaType === 'video' && videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
    }
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  };

  const handleTimeUpdate = (e: React.SyntheticEvent<HTMLVideoElement | HTMLAudioElement>) => {
    const target = e.currentTarget;
    setCurrentTime(target.currentTime);
    setDuration(target.duration);
  };

  const handleSeek = (newTime: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = newTime;
    }
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
    }
    setCurrentTime(newTime);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const downloadMedia = () => {
    if (!media) return;
    
    const link = document.createElement('a');
    link.href = media.url;
    link.download = media.original_filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const openInNewTab = () => {
    if (!media) return;
    window.open(media.url, '_blank');
  };

  if (!media) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4">
      <div 
        ref={modalRef}
        className={`relative max-w-full max-h-full ${isFullscreen ? 'w-full h-full' : 'w-fit h-fit'} flex flex-col`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 bg-black/50 text-white">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-medium truncate">{media.title}</h3>
            <p className="text-sm text-gray-300 truncate">
              {media.workspace_name} • {media.format?.toUpperCase()} • {media.mediaType}
            </p>
          </div>
          
          <div className="flex items-center space-x-2 ml-4">
            {/* Navigation */}
            {allMedia.length > 1 && (
              <>
                <button
                  onClick={() => onNavigate?.(currentIndex - 1)}
                  disabled={currentIndex === 0}
                  className="p-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Previous media"
                >
                  <SkipBack className="w-4 h-4" />
                </button>
                <span className="text-sm text-gray-300">
                  {currentIndex + 1} of {allMedia.length}
                </span>
                <button
                  onClick={() => onNavigate?.(currentIndex + 1)}
                  disabled={currentIndex === allMedia.length - 1}
                  className="p-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Next media"
                >
                  <SkipForward className="w-4 h-4" />
                </button>
              </>
            )}
            
            {/* Actions */}
            <button
              onClick={downloadMedia}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20"
              title="Download"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={openInNewTab}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20"
              title="Open in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20"
              title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Media Content */}
        <div className="flex-1 flex items-center justify-center bg-black min-h-0">
          {media.mediaType === 'image' ? (
            <div className="relative max-w-full max-h-full flex items-center justify-center">
              {!imageError ? (
                <img
                  src={media.url}
                  alt={media.title}
                  className={`max-w-full max-h-full object-contain ${isFullscreen ? 'w-full h-full' : ''}`}
                  onError={() => setImageError(true)}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <div className="flex flex-col items-center justify-center p-8 text-gray-400">
                  <div className="text-6xl mb-4">🖼️</div>
                  <p className="text-lg">Failed to load image</p>
                  <p className="text-sm mt-2">The image file might be corrupted or unavailable</p>
                </div>
              )}
            </div>
          ) : media.mediaType === 'video' ? (
            <div className="relative w-full h-full flex flex-col">
              <div className="flex-1 flex items-center justify-center">
                <video
                  ref={videoRef}
                  src={media.url}
                  className={`max-w-full max-h-full ${isFullscreen ? 'w-full h-full' : ''}`}
                  onTimeUpdate={handleTimeUpdate}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onLoadedMetadata={handleTimeUpdate}
                  controls={false}
                  onClick={togglePlay}
                />
              </div>
              
              {/* Video Controls */}
              <div className="bg-black/50 p-4">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={togglePlay}
                    className="p-2 rounded-lg bg-white/10 hover:bg-white/20"
                  >
                    {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                  </button>
                  
                  <button
                    onClick={toggleMute}
                    className="p-2 rounded-lg bg-white/10 hover:bg-white/20"
                  >
                    {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                  </button>
                  
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={volume}
                    onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                    className="w-20"
                  />
                  
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max={duration || 0}
                      value={currentTime}
                      onChange={(e) => handleSeek(parseFloat(e.target.value))}
                      className="w-full"
                    />
                  </div>
                  
                  <span className="text-white text-sm min-w-[80px]">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            // Audio or unknown format
            <div className="flex flex-col items-center justify-center p-8 text-white">
              <div className="text-6xl mb-4">
                {media.format && ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(media.format) ? '🎵' : '📁'}
              </div>
              <h3 className="text-xl font-medium mb-2">{media.title}</h3>
              <p className="text-gray-400 mb-4">{media.format?.toUpperCase()} file</p>
              
              {/* Audio player for audio files */}
              {media.format && ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(media.format) && (
                <div className="w-full max-w-md">
                  <audio
                    ref={audioRef}
                    src={media.url}
                    onTimeUpdate={handleTimeUpdate}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                    onLoadedMetadata={handleTimeUpdate}
                    className="hidden"
                  />
                  
                  <div className="bg-white/10 rounded-lg p-4">
                    <div className="flex items-center space-x-4">
                      <button
                        onClick={() => {
                          if (audioRef.current) {
                            if (isPlaying) {
                              audioRef.current.pause();
                            } else {
                              audioRef.current.play();
                            }
                          }
                        }}
                        className="p-3 rounded-full bg-purple-500 hover:bg-purple-600"
                      >
                        {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
                      </button>
                      
                      <div className="flex-1">
                        <input
                          type="range"
                          min="0"
                          max={duration || 0}
                          value={currentTime}
                          onChange={(e) => handleSeek(parseFloat(e.target.value))}
                          className="w-full"
                        />
                        <div className="flex justify-between text-sm text-gray-400 mt-1">
                          <span>{formatTime(currentTime)}</span>
                          <span>{formatTime(duration)}</span>
                        </div>
                      </div>
                      
                      <button
                        onClick={toggleMute}
                        className="p-2 rounded-lg bg-white/10 hover:bg-white/20"
                      >
                        {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Background click to close */}
      <div 
        className="absolute inset-0 -z-10" 
        onClick={onClose}
      />
    </div>
  );
}