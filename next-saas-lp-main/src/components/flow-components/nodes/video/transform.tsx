import { generateVideoAction } from '@/app/actions/ai';
import { NodeLayout } from '@/components/flow-components/nodes/layout';
import { Button } from '@/components/flow-components/ui/button';
import { Skeleton } from '@/components/flow-components/ui/skeleton';
import { Textarea } from '@/components/flow-components/ui/textarea';
import { useAnalytics } from '@/hooks/use-analytics';
import { download } from '@/lib/download';
import { handleError } from '@/lib/error/handle';
import { videoModels } from '@/lib/models/video';
import { getImagesFromImageNodes, getTextFromTextNodes } from '@/lib/xyflow';
import { urlsToBase64DataUrls } from '@/lib/image-utils';
import { useProject } from '@/providers/project-provider';
import { getIncomers, useReactFlow } from '@xyflow/react';
import {
  ClockIcon,
  DownloadIcon,
  Loader2Icon,
  PlayIcon,
  RotateCcwIcon,
} from 'lucide-react';
import Image from 'next/image';
import { type ChangeEventHandler, type ComponentProps, useState } from 'react';
import { toast } from 'sonner';
import { mutate } from 'swr';
import type { VideoNodeProps } from '.';
import { ModelSelector } from '../model-selector';
import { VideoSizeSelector } from './video-size-selector';
import { VideoDurationSelector } from './video-duration-selector';

type VideoTransformProps = VideoNodeProps & {
  title: string;
};

const getDefaultModel = (models: typeof videoModels) => {
  const defaultModel = Object.entries(models).find(
    ([_, model]) => model.default
  );

  if (!defaultModel) {
    throw new Error('No default model found');
  }

  return defaultModel[0];
};

export const VideoTransform = ({
  data,
  id,
  type,
  title,
}: VideoTransformProps) => {
  const { updateNodeData, getNodes, getEdges } = useReactFlow();
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState('');
  const { project } = useProject();
  const modelId = data.model ?? getDefaultModel(videoModels);
  const videoSize = data.size ?? '1280x720';
  const videoDuration = data.seconds ?? 8;
  const analytics = useAnalytics();
  
  // Check if model supports configuration (Sora models)
  const isSoraModel = modelId === 'sora-2' || modelId === 'sora-2-pro';
  const modelConfig = videoModels[modelId];
  
  // Get incoming media from connected nodes
  const incomers = getIncomers({ id }, getNodes(), getEdges());
  const incomingImages = getImagesFromImageNodes(incomers);
  const incomingVideos = incomers
    .filter((node) => node.type === 'video' && node.data.content)
    .map((node) => (node.data as any).content as { url: string; type: string });
  
  // Combine uploaded video/image with incoming media as references
  const allReferenceMedia = [
    ...(data.content ? [data.content] : []),
    ...incomingImages,
    ...incomingVideos,
  ];

  const handleGenerate = async () => {
    if (loading || !project?.id) {
      return;
    }

    try {
      const textPrompts = getTextFromTextNodes(incomers);
      
      // Build combined prompt: instructions + all text prompts
      const promptParts = [];
      if (data.instructions) {
        promptParts.push(data.instructions);
      }
      promptParts.push(...textPrompts);
      const combinedPrompt = promptParts.join('\n\n');

      console.log('🎬 VIDEO NODE GENERATING:', {
        nodeId: id,
        nodeType: type,
        incomingNodes: incomers.map(n => ({ id: n.id, type: n.type, data: n.data })),
        textPrompts,
        textPromptsCount: textPrompts.length,
        uploadedMedia: data.content,
        incomingImages: incomingImages,
        incomingVideos: incomingVideos,
        allReferenceMedia: allReferenceMedia,
        totalReferenceMedia: allReferenceMedia.length,
        instructions: data.instructions,
        combinedPrompt,
        model: modelId,
      });

      if (!combinedPrompt && !allReferenceMedia.length) {
        throw new Error('No input provided (need text prompt or reference media)');
      }

      setLoading(true);
      setProgress(0);
      setProgressStatus('Preparing...');

      analytics.track('canvas', 'node', 'generate', {
        type,
        promptLength: combinedPrompt.length,
        textPromptsLength: textPrompts.length,
        model: modelId,
        instructionsLength: data.instructions?.length ?? 0,
        referenceMediaCount: allReferenceMedia.length,
        hasUploadedMedia: !!data.content,
      });

      // Convert blob URLs to base64 before sending to server
      const referenceMediaBase64 = await urlsToBase64DataUrls(allReferenceMedia);

      setProgressStatus('Submitting...');

      const response = await generateVideoAction({
        modelId,
        prompt: combinedPrompt,
        referenceMedia: referenceMediaBase64,
        nodeId: id,
        projectId: project.id,
        size: videoSize,
        seconds: videoDuration,
      });

      if ('error' in response) {
        throw new Error(response.error);
      }

      updateNodeData(id, response.nodeData);

      toast.success('Video generated successfully');

      setTimeout(() => mutate('credits'), 5000);
    } catch (error) {
      handleError('Error generating video', error);
    } finally {
      setLoading(false);
      setProgress(0);
      setProgressStatus('');
    }
  };

  const toolbar: ComponentProps<typeof NodeLayout>['toolbar'] = [
    {
      children: (
        <ModelSelector
          value={modelId}
          options={videoModels}
          key={id}
          className="w-[200px] rounded-md h-9"
          onChange={(value) => updateNodeData(id, { model: value })}
        />
      ),
    },
    // Add size selector for Sora models
    ...(isSoraModel && modelConfig.sizes
      ? [
          {
            children: (
              <VideoSizeSelector
                value={videoSize}
                modelId={modelId}
                onChange={(value) => updateNodeData(id, { size: value })}
                className="w-[120px] rounded-md h-9"
              />
            ),
          },
        ]
      : []),
    // Add duration selector for Sora models
    ...(isSoraModel && modelConfig.durations
      ? [
          {
            children: (
              <VideoDurationSelector
                value={videoDuration}
                modelId={modelId}
                onChange={(value) => updateNodeData(id, { seconds: value })}
                className="w-[80px] rounded-md h-9"
              />
            ),
          },
        ]
      : []),
    loading
      ? {
          tooltip: 'Generating...',
          children: (
            <Button size="icon" className="rounded-md h-9" disabled>
              <Loader2Icon className="animate-spin" size={12} />
            </Button>
          ),
        }
      : {
          tooltip: data.generated?.url ? 'Regenerate' : 'Generate',
          children: (
            <Button
              size="icon"
              className="rounded-md h-9"
              onClick={handleGenerate}
              disabled={loading || !project?.id}
            >
              {data.generated?.url ? (
                <RotateCcwIcon size={12} />
              ) : (
                <PlayIcon size={12} />
              )}
            </Button>
          ),
        },
  ];

  if (data.generated?.url) {
    toolbar.push({
      tooltip: 'Download',
      children: (
        <Button
          variant="ghost"
          size="icon"
          className="rounded-md h-9"
          onClick={() => download(data.generated, id, 'mp4')}
        >
          <DownloadIcon size={12} />
        </Button>
      ),
    });
  }

  if (data.updatedAt) {
    toolbar.push({
      tooltip: `Last updated: ${new Intl.DateTimeFormat('en-US', {
        dateStyle: 'short',
        timeStyle: 'short',
      }).format(new Date(data.updatedAt))}`,
      children: (
        <Button size="icon" variant="ghost" className="rounded-md h-9">
          <ClockIcon size={12} />
        </Button>
      ),
    });
  }

  const handleInstructionsChange: ChangeEventHandler<HTMLTextAreaElement> = (
    event
  ) => updateNodeData(id, { instructions: event.target.value });

  return (
    <NodeLayout id={id} data={data} type={type} title={title} toolbar={toolbar}>
      {/* Reference Media Preview */}
      {allReferenceMedia.length > 0 && (
        <div className="border-b border-border bg-secondary/50 p-3">
          <p className="text-xs text-muted-foreground mb-2">
            🎬 Reference Media ({allReferenceMedia.length})
          </p>
          <div className="flex gap-2 flex-wrap">
            {allReferenceMedia.map((media, idx) => (
              <div key={idx} className="relative w-16 h-16 rounded-lg overflow-hidden border border-border">
                {media.type.startsWith('image') ? (
                  <Image
                    src={media.url}
                    alt={`Reference ${idx + 1}`}
                    width={64}
                    height={64}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <video
                    src={media.url}
                    className="w-full h-full object-cover"
                    muted
                  />
                )}
                <div className="absolute top-0 right-0 bg-black/70 text-white text-[10px] px-1">
                  {idx === 0 && data.content ? '📤' : '🔗'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {loading && (
        <div className="flex aspect-video w-full items-center justify-center rounded-b-xl bg-secondary/50 relative">
          <div className="absolute inset-0 flex flex-col items-center justify-center space-y-3 z-10">
            <Loader2Icon
              size={32}
              className="animate-spin text-primary"
            />
            <div className="text-center space-y-1">
              <p className="text-sm font-medium">
                {progressStatus || 'Generating...'}
              </p>
              {isSoraModel && (
                <p className="text-xs text-muted-foreground">
                  {videoSize} • {videoDuration}s • {modelConfig.label}
                </p>
              )}
            </div>
            {progress > 0 && (
              <div className="w-48 h-2 bg-secondary rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            )}
          </div>
        </div>
      )}
      {!loading && !data.generated?.url && (
        <div className="flex aspect-video w-full items-center justify-center rounded-b-xl bg-secondary">
          <p className="text-muted-foreground text-sm">
            Press <PlayIcon size={12} className="-translate-y-px inline" /> to
            generate video
          </p>
        </div>
      )}
      {data.generated?.url && !loading && (
        <video
          src={data.generated.url}
          width={data.width ?? 800}
          height={data.height ?? 450}
          autoPlay
          muted
          loop
          playsInline
          className="w-full rounded-b-xl object-cover"
        />
      )}
      <Textarea
        value={data.instructions ?? ''}
        onChange={handleInstructionsChange}
        placeholder="Enter instructions"
        className="shrink-0 resize-none rounded-none border-none bg-transparent! shadow-none focus-visible:ring-0"
      />
    </NodeLayout>
  );
};

