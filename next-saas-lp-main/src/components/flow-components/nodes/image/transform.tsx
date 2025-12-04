import { generateImageAction, editImageAction } from '@/app/actions/ai';
import { NodeLayout } from '@/components/flow-components/nodes/layout';
import { Button } from '@/components/flow-components/ui/button';
import { Skeleton } from '@/components/flow-components/ui/skeleton';
import { Textarea } from '@/components/flow-components/ui/textarea';
import { useAnalytics } from '@/hooks/use-analytics';
import { download } from '@/lib/download';
import { handleError } from '@/lib/error/handle';
import { imageModels } from '@/lib/models/image';
import { urlsToBase64DataUrls } from '@/lib/image-utils';
import { getImagesFromImageNodes, getTextFromTextNodes } from '@/lib/xyflow';
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
import {
  type ChangeEventHandler,
  type ComponentProps,
  useCallback,
  useMemo,
  useState,
} from 'react';
import { toast } from 'sonner';
import { mutate } from 'swr';
import type { ImageNodeProps } from '.';
import { ModelSelector } from '../model-selector';
import { ImageSizeSelector } from './image-size-selector';

type ImageTransformProps = ImageNodeProps & {
  title: string;
};

const getDefaultModel = (models: typeof imageModels) => {
  const defaultModel = Object.entries(models).find(
    ([_, model]) => model.default
  );

  if (!defaultModel) {
    throw new Error('No default model found');
  }

  return defaultModel[0];
};

export const ImageTransform = ({
  data,
  id,
  type,
  title,
}: ImageTransformProps) => {
  const { updateNodeData, getNodes, getEdges } = useReactFlow();
  const [loading, setLoading] = useState(false);
  const { project } = useProject();
  const incomingImages = getImagesFromImageNodes(getIncomers({ id }, getNodes(), getEdges()));
  const hasIncomingImageNodes = incomingImages.length > 0;
  const modelId = data.model ?? getDefaultModel(imageModels);
  const analytics = useAnalytics();
  const selectedModel = imageModels[modelId];
  const size = data.size ?? selectedModel?.sizes?.at(0);
  
  // Combine uploaded image with incoming images for reference
  const allReferenceImages = [
    ...(data.content ? [data.content] : []),
    ...incomingImages,
  ];

  const handleGenerate = useCallback(async () => {
    if (loading || !project?.id) {
      return;
    }

    const incomers = getIncomers({ id }, getNodes(), getEdges());
    const textNodes = getTextFromTextNodes(incomers);
    
    // Build combined prompt: instructions + all text prompts
    const promptParts = [];
    if (data.instructions) {
      promptParts.push(data.instructions);
    }
    promptParts.push(...textNodes);
    const combinedPrompt = promptParts.join('\n\n');

    console.log('🎨 IMAGE NODE GENERATING:', {
      nodeId: id,
      nodeType: type,
      incomingNodes: incomers.map(n => ({ id: n.id, type: n.type, data: n.data })),
      textPrompts: textNodes,
      textPromptsCount: textNodes.length,
      uploadedImage: data.content,
      incomingImages: incomingImages,
      allReferenceImages: allReferenceImages,
      totalReferenceImages: allReferenceImages.length,
      instructions: data.instructions,
      combinedPrompt,
      model: modelId,
      size,
    });

    try {
      if (!combinedPrompt && !allReferenceImages.length) {
        throw new Error('No input provided (need text prompt or reference images)');
      }

      setLoading(true);

      analytics.track('canvas', 'node', 'generate', {
        type,
        textPromptsLength: textNodes.length,
        imagePromptsLength: allReferenceImages.length,
        hasUploadedImage: !!data.content,
        model: modelId,
        instructionsLength: data.instructions?.length ?? 0,
      });

      // Get auth token from localStorage
      const authToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      
      let response;
      
      if (allReferenceImages.length) {
        // Convert blob URLs to base64 data URLs before sending to server
        console.log('🔄 Converting blob URLs to base64...');
        const base64Images = await urlsToBase64DataUrls(allReferenceImages);
        console.log('✅ Conversion complete:', {
          originalCount: allReferenceImages.length,
          convertedCount: base64Images.length,
          samples: base64Images.map(img => ({
            type: img.type,
            urlPrefix: img.url.substring(0, 50) + '...',
          })),
        });
        
        response = await editImageAction({
          images: base64Images,
          prompt: combinedPrompt,
          nodeId: id,
          projectId: project.id,
          modelId,
          size,
          authToken: authToken || undefined,
        });
      } else {
        response = await generateImageAction({
          prompt: combinedPrompt,
          modelId,
          instructions: data.instructions,
          projectId: project.id,
          nodeId: id,
          size,
          authToken: authToken || undefined,
        });
      }

      if ('error' in response) {
        throw new Error(response.error);
      }

      updateNodeData(id, response.nodeData);

      toast.success('Image generated successfully');

      setTimeout(() => mutate('credits'), 5000);
    } catch (error) {
      handleError('Error generating image', error);
    } finally {
      setLoading(false);
    }
  }, [
    loading,
    project?.id,
    size,
    id,
    analytics,
    type,
    data.instructions,
    data.content,
    getEdges,
    modelId,
    getNodes,
    updateNodeData,
    allReferenceImages,
    incomingImages,
  ]);

  const handleInstructionsChange: ChangeEventHandler<HTMLTextAreaElement> = (
    event
  ) => updateNodeData(id, { instructions: event.target.value });

  const toolbar = useMemo<ComponentProps<typeof NodeLayout>['toolbar']>(() => {
    const availableModels = Object.fromEntries(
      Object.entries(imageModels).map(([key, model]) => [
        key,
        {
          ...model,
          disabled: hasIncomingImageNodes
            ? !model.supportsEdit
            : model.disabled,
        },
      ])
    );

    const items: ComponentProps<typeof NodeLayout>['toolbar'] = [
      {
        children: (
          <ModelSelector
            value={modelId}
            options={availableModels}
            id={id}
            className="w-[200px]"
            onChange={(value) => updateNodeData(id, { model: value })}
          />
        ),
      },
    ];

    if (selectedModel?.sizes?.length) {
      items.push({
        children: (
          <ImageSizeSelector
            value={size ?? ''}
            options={selectedModel?.sizes ?? []}
            id={id}
            className="w-[200px]"
            onChange={(value) => updateNodeData(id, { size: value })}
          />
        ),
      });
    }

    items.push(
      loading
        ? {
            tooltip: 'Generating...',
            children: (
              <Button size="icon" className="rounded-md h-9 w-9" disabled>
                <Loader2Icon className="animate-spin" size={12} />
              </Button>
            ),
          }
        : {
            tooltip: data.generated?.url ? 'Regenerate' : 'Generate',
            children: (
              <Button
                size="icon"
                className="rounded-md h-9 w-9"
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
          }
    );

    if (data.generated) {
      items.push({
        tooltip: 'Download',
        children: (
          <Button
            variant="ghost"
            size="icon"
            className="rounded-md h-9 w-9"
            onClick={() => download(data.generated, id, 'png')}
          >
            <DownloadIcon size={12} />
          </Button>
        ),
      });
    }

    if (data.updatedAt) {
      items.push({
        tooltip: `Last updated: ${new Intl.DateTimeFormat('en-US', {
          dateStyle: 'short',
          timeStyle: 'short',
        }).format(new Date(data.updatedAt))}`,
        children: (
          <Button size="icon" variant="ghost" className="rounded-md h-9 w-9">
            <ClockIcon size={12} />
          </Button>
        ),
      });
    }

    return items;
  }, [
    modelId,
    hasIncomingImageNodes,
    id,
    updateNodeData,
    selectedModel?.sizes,
    size,
    loading,
    data.generated,
    data.updatedAt,
    handleGenerate,
    project?.id,
  ]);

  const aspectRatio = useMemo(() => {
    if (!data.size) {
      return '1/1';
    }

    const [width, height] = data.size.split('x').map(Number);
    return `${width}/${height}`;
  }, [data.size]);

  return (
    <NodeLayout id={id} data={data} type={type} title={title} toolbar={toolbar}>
      {/* Reference Images Preview */}
      {allReferenceImages.length > 0 && (
        <div className="border-b border-border bg-secondary/50 p-3">
          <p className="text-xs text-muted-foreground mb-2">
            📸 Reference Images ({allReferenceImages.length})
          </p>
          <div className="flex gap-2 flex-wrap">
            {allReferenceImages.map((img, idx) => (
              <div key={idx} className="relative w-16 h-16 rounded-lg overflow-hidden border border-border">
                <Image
                  src={img.url}
                  alt={`Reference ${idx + 1}`}
                  width={64}
                  height={64}
                  className="w-full h-full object-cover"
                />
                <div className="absolute top-0 right-0 bg-black/70 text-white text-[10px] px-1">
                  {idx === 0 && data.content ? '📤' : '🔗'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {loading && (
        <Skeleton
          className="flex w-full animate-pulse items-center justify-center rounded-b-xl"
          style={{ aspectRatio }}
        >
          <Loader2Icon
            size={16}
            className="size-4 animate-spin text-muted-foreground"
          />
        </Skeleton>
      )}
      {!loading && !data.generated?.url && (
        <div
          className="flex w-full items-center justify-center rounded-b-xl bg-secondary p-4"
          style={{ aspectRatio }}
        >
          <p className="text-muted-foreground text-sm">
            Press <PlayIcon size={12} className="-translate-y-px inline" /> to
            create an image
          </p>
        </div>
      )}
      {!loading && data.generated?.url && (
        <Image
          src={data.generated.url}
          alt="Generated image"
          width={1000}
          height={1000}
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

