"use client";

import { useState } from 'react';
import { Upload, X, Image as ImageIcon, Video, Trash2, Download } from 'lucide-react';
import { useInstagramImageUpload } from '@/hooks/use-instagram';
import { toast } from 'sonner';

interface ImageGalleryProps {
  onImageSelect?: (imageUrl: string) => void;
  selectedImage?: string;
  maxSelection?: number;
  showUpload?: boolean;
}

export function ImageGallery({ 
  onImageSelect, 
  selectedImage, 
  maxSelection = 1, 
  showUpload = true 
}: ImageGalleryProps) {
  const { uploads, isLoading, uploadImage, deleteUpload, refetch } = useInstagramImageUpload();
  const [uploading, setUploading] = useState(false);

  const handleFileUpload = async (files: FileList) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    const file = files[0];

    // Validate file type (images and videos)
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
      toast.error('Please select an image or video file');
      setUploading(false);
      return;
    }

    // Validate file size (100MB limit for videos, 10MB for images)
    const maxSize = file.type.startsWith('video/') ? 100 * 1024 * 1024 : 10 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error(`File size must be less than ${file.type.startsWith('video/') ? '100MB' : '10MB'}`);
      setUploading(false);
      return;
    }

    try {
      await uploadImage(file);
      toast.success('File uploaded successfully!');
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      handleFileUpload(files);
    }
  };

  const handleImageSelect = (imageUrl: string) => {
    if (onImageSelect) {
      onImageSelect(imageUrl);
    }
  };

  const handleDelete = async (imageId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (confirm('Are you sure you want to delete this file?')) {
      await deleteUpload(imageId);
      toast.success('File deleted');
    }
  };

  const downloadImage = async (imageUrl: string, filename: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Download started');
    } catch (error) {
      toast.error('Failed to download file');
    }
  };

  const isVideo = (url: string) => {
    return url.match(/\.(mp4|mov|avi|webm)$/i);
  };

  if (isLoading) {
    return (
      <div className="bg-[#1a1a1a] border border-white/10 rounded-lg p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          <span className="ml-3 text-gray-400">Loading media...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#1a1a1a] border border-white/10 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Media Library</h3>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">{uploads.length} files</span>
          <button
            onClick={refetch}
            className="text-purple-400 hover:text-purple-300 text-sm"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Upload Section */}
      {showUpload && (
        <div className="mb-6">
          <label className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white px-6 py-3 rounded-lg font-medium transition inline-flex items-center gap-2 cursor-pointer">
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Uploading...</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>Upload Media</span>
              </>
            )}
            <input
              type="file"
              accept="image/*,video/*"
              onChange={handleFileInput}
              className="hidden"
              disabled={uploading}
            />
          </label>
          <p className="text-xs text-gray-500 mt-2">Images (JPG, PNG up to 10MB) or Videos (MP4, MOV up to 100MB)</p>
        </div>
      )}

      {/* Media Grid */}
      {!Array.isArray(uploads) || uploads.length === 0 ? (
        <div className="text-center py-12">
          <ImageIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-400 mb-2">No media yet</h4>
          <p className="text-sm text-gray-500">
            {showUpload ? 'Upload your first image or video to get started' : 'No media in your library'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {uploads.map((upload) => (
            <div
              key={upload.id}
              className={`relative group aspect-square rounded-lg overflow-hidden cursor-pointer border-2 transition ${
                selectedImage === upload.image_url
                  ? 'border-purple-500'
                  : 'border-white/10 hover:border-white/30'
              }`}
              onClick={() => handleImageSelect(upload.image_url)}
            >
              {isVideo(upload.image_url) ? (
                <video
                  src={upload.image_url}
                  className="w-full h-full object-cover"
                  muted
                  playsInline
                />
              ) : (
                <img
                  src={upload.image_url}
                  alt="Uploaded media"
                  className="w-full h-full object-cover"
                />
              )}
              
              {/* Video indicator */}
              {isVideo(upload.image_url) && (
                <div className="absolute top-2 left-2 bg-black/70 p-1.5 rounded">
                  <Video className="w-4 h-4 text-white" />
                </div>
              )}
              
              {/* Overlay */}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <div className="flex gap-2">
                  <button
                    onClick={(e) => downloadImage(
                      upload.image_url, 
                      `media-${upload.id}${isVideo(upload.image_url) ? '.mp4' : '.jpg'}`, 
                      e
                    )}
                    className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition"
                    title="Download"
                  >
                    <Download className="w-4 h-4 text-white" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(upload.id, e)}
                    className="p-2 bg-red-500/20 rounded-full hover:bg-red-500/30 transition"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
                  </button>
                </div>
              </div>

              {/* Selection indicator */}
              {selectedImage === upload.image_url && (
                <div className="absolute top-2 right-2 w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
              
              {/* Upload date */}
              <div className="absolute bottom-2 left-2 text-xs text-white bg-black/50 px-2 py-1 rounded">
                {new Date(upload.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface ImageUploadBoxProps {
  onImageUpload: (imageUrl: string) => void;
  currentImage?: string;
  className?: string;
}

export function ImageUploadBox({ onImageUpload, currentImage, className = "" }: ImageUploadBoxProps) {
  const [uploading, setUploading] = useState(false);
  const { uploadImage } = useInstagramImageUpload();

  const handleFileUpload = async (files: FileList) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    const file = files[0];

    // Validate file type (images and videos)
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
      toast.error('Please select an image or video file');
      setUploading(false);
      return;
    }

    // Validate file size (100MB limit for videos, 10MB for images)
    const maxSize = file.type.startsWith('video/') ? 100 * 1024 * 1024 : 10 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error(`File size must be less than ${file.type.startsWith('video/') ? '100MB' : '10MB'}`);
      setUploading(false);
      return;
    }

    try {
      const result = await uploadImage(file);
      onImageUpload(result.url);
      toast.success('File uploaded successfully!');
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      handleFileUpload(files);
    }
  };

  const isVideo = (url: string) => {
    return url.match(/\.(mp4|mov|avi|webm)$/i);
  };

  if (currentImage && !uploading) {
    return (
      <div className={`relative ${className}`}>
        {isVideo(currentImage) ? (
          <video
            src={currentImage}
            controls
            className="w-full h-full object-cover rounded-lg"
          />
        ) : (
          <img
            src={currentImage}
            alt="Selected media"
            className="w-full h-full object-cover rounded-lg"
          />
        )}
        <button
          onClick={() => onImageUpload('')}
          className="absolute top-2 right-2 p-1 bg-red-500 rounded-full text-white hover:bg-red-600 transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className={`border-2 border-dashed rounded-lg p-6 text-center ${className}`}>
      {uploading ? (
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mb-3"></div>
          <p className="text-sm text-gray-400">Uploading...</p>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          <div className="flex items-center gap-2 mb-2">
            <ImageIcon className="w-8 h-8 text-gray-400" />
            <Video className="w-8 h-8 text-gray-400" />
          </div>
          <label className="bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white px-4 py-2 rounded-lg text-sm font-medium transition cursor-pointer inline-flex items-center gap-2">
            <Upload className="w-4 h-4" />
            <span>Choose Media</span>
            <input
              type="file"
              accept="image/*,video/*"
              onChange={handleFileInput}
              className="hidden"
              disabled={uploading}
            />
          </label>
          <p className="text-xs text-gray-500 mt-2">Images (up to 10MB) or Videos (up to 100MB)</p>
        </div>
      )}
    </div>
  );
}
