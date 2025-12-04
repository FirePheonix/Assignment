'use client';

import { useState, useCallback } from 'react';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Upload, X, Image as ImageIcon, Video, Globe, Lock } from 'lucide-react';
import { workspaceApi } from '@/lib/workspace-api';
import type { Workspace, WorkspaceMedia } from '@/lib/workspace-api';
import { toast } from 'sonner';

interface PublishDialogProps {
  workspace: Workspace;
  onPublish?: (workspace: Workspace) => void;
}

export function PublishDialog({ workspace, onPublish }: PublishDialogProps) {
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState(workspace.description || '');
  const [mediaFiles, setMediaFiles] = useState<File[]>([]);
  const [mediaPreviews, setMediaPreviews] = useState<string[]>([]);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter(file => 
      file.type.startsWith('image/') || file.type.startsWith('video/')
    );

    if (validFiles.length !== files.length) {
      toast.error('Only image and video files are allowed');
    }

    setMediaFiles(prev => [...prev, ...validFiles]);

    // Create previews
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e) => {
        setMediaPreviews(prev => [...prev, e.target?.result as string]);
      };
      reader.readAsDataURL(file);
    });
  }, []);

  const handleRemoveMedia = useCallback((index: number) => {
    setMediaFiles(prev => prev.filter((_, i) => i !== index));
    setMediaPreviews(prev => prev.filter((_, i) => i !== index));
  }, []);

  const handlePublish = useCallback(async () => {
    try {
      setIsPublishing(true);

      // First, publish the workspace
      const publishedWorkspace = await workspaceApi.publish(workspace.id, description);
      toast.success('Workspace published!');

      // Then upload media files
      if (mediaFiles.length > 0) {
        setIsUploading(true);
        
        for (const file of mediaFiles) {
          const mediaType = file.type.startsWith('image/') ? 'image' : 'video';
          await workspaceApi.uploadMedia(
            workspace.id,
            file,
            mediaType,
            file.name
          );
        }

        toast.success(`${mediaFiles.length} media file(s) uploaded!`);
      }

      // Callback with updated workspace
      if (onPublish) {
        // Fetch the updated workspace with media
        const updated = await workspaceApi.get(workspace.id);
        onPublish(updated);
      }

      setOpen(false);
      setMediaFiles([]);
      setMediaPreviews([]);
    } catch (error) {
      console.error('Error publishing:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to publish workspace');
    } finally {
      setIsPublishing(false);
      setIsUploading(false);
    }
  }, [workspace.id, description, mediaFiles, onPublish]);

  const handleUnpublish = useCallback(async () => {
    try {
      setIsPublishing(true);
      const unpublishedWorkspace = await workspaceApi.unpublish(workspace.id);
      toast.success('Workspace unpublished');
      
      if (onPublish) {
        onPublish(unpublishedWorkspace);
      }
      
      setOpen(false);
    } catch (error) {
      console.error('Error unpublishing:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to unpublish workspace');
    } finally {
      setIsPublishing(false);
    }
  }, [workspace.id, onPublish]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button 
          variant={workspace.isPublic ? "outline" : "default"} 
          size="sm"
          className="gap-2"
        >
          {workspace.isPublic ? (
            <>
              <Globe className="h-4 w-4" />
              Published
            </>
          ) : (
            <>
              <Lock className="h-4 w-4" />
              Publish
            </>
          )}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>
            {workspace.isPublic ? 'Manage Published Workspace' : 'Publish Workspace'}
          </DialogTitle>
          <DialogDescription>
            {workspace.isPublic 
              ? 'Your workspace is publicly accessible. You can update details or unpublish it.'
              : 'Make this workspace publicly accessible. Add AI-generated images/videos to showcase your work.'
            }
          </DialogDescription>
        </DialogHeader>

        {workspace.isPublic && (
          <div className="rounded-lg bg-green-500/10 border border-green-500/20 p-4">
            <p className="text-sm text-green-500">
              <Globe className="h-4 w-4 inline mr-2" />
              Live at: <a href={`/flow-generator/${workspace.slug}`} target="_blank" className="underline font-mono">/flow-generator/{workspace.slug}</a>
            </p>
            {workspace.viewCount > 0 && (
              <p className="text-sm text-muted-foreground mt-2">
                {workspace.viewCount} views · {workspace.cloneCount} imports
              </p>
            )}
          </div>
        )}

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe what this workflow does..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label>Media (Images/Videos)</Label>
            <div className="border-2 border-dashed rounded-lg p-4">
              <input
                type="file"
                id="media-upload"
                multiple
                accept="image/*,video/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              <label
                htmlFor="media-upload"
                className="flex flex-col items-center justify-center cursor-pointer"
              >
                <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">
                  Click to upload images or videos
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  AI-generated content from your workflow
                </p>
              </label>
            </div>

            {/* Media Previews */}
            {mediaPreviews.length > 0 && (
              <div className="grid grid-cols-3 gap-2 mt-4">
                {mediaPreviews.map((preview, index) => (
                  <div key={index} className="relative aspect-square rounded-lg overflow-hidden border">
                    {mediaFiles[index].type.startsWith('image/') ? (
                      <img
                        src={preview}
                        alt={`Preview ${index + 1}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-muted flex items-center justify-center">
                        <Video className="h-8 w-8 text-muted-foreground" />
                      </div>
                    )}
                    <button
                      onClick={() => handleRemoveMedia(index)}
                      className="absolute top-1 right-1 p-1 bg-black/50 rounded-full hover:bg-black/70"
                    >
                      <X className="h-4 w-4 text-white" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Existing Media */}
            {workspace.media && workspace.media.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium mb-2">Existing Media</p>
                <div className="grid grid-cols-3 gap-2">
                  {workspace.media.map((media) => (
                    <div key={media.id} className="relative aspect-square rounded-lg overflow-hidden border">
                      {media.mediaType === 'image' ? (
                        <img
                          src={media.fileUrl}
                          alt={media.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-muted flex items-center justify-center">
                          <Video className="h-8 w-8 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          {workspace.isPublic ? (
            <>
              <Button
                variant="destructive"
                onClick={handleUnpublish}
                disabled={isPublishing}
              >
                Unpublish
              </Button>
              <Button onClick={handlePublish} disabled={isPublishing || isUploading}>
                {isUploading ? 'Uploading...' : isPublishing ? 'Saving...' : 'Update'}
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handlePublish} disabled={isPublishing || isUploading}>
                {isUploading ? 'Uploading...' : isPublishing ? 'Publishing...' : 'Publish'}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
