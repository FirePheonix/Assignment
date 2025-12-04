import { NodeLayout } from '@/components/flow-components/nodes/layout';
import { DropzoneEmptyState } from '@/components/flow-components/ui/kibo-ui/dropzone';
import { DropzoneContent } from '@/components/flow-components/ui/kibo-ui/dropzone';
import { Dropzone } from '@/components/flow-components/ui/kibo-ui/dropzone';
import { Skeleton } from '@/components/flow-components/ui/skeleton';
import { handleError } from '@/lib/error/handle';
import { uploadFile } from '@/lib/upload';
import { useProject } from '@/providers/project-provider';
import { useReactFlow } from '@xyflow/react';
import { Loader2Icon } from 'lucide-react';
import Image from 'next/image';
import { useState } from 'react';
import type { ImageNodeProps } from '.';

type ImagePrimitiveProps = ImageNodeProps & {
  title: string;
};

export const ImagePrimitive = ({
  data,
  id,
  type,
  title,
}: ImagePrimitiveProps) => {
  const { updateNodeData } = useReactFlow();
  const { project } = useProject();
  const [files, setFiles] = useState<File[] | undefined>();
  const [isUploading, setIsUploading] = useState(false);

  const handleDrop = async (files: File[]) => {
    if (isUploading || !project?.id) {
      return;
    }

    try {
      if (!files.length) {
        throw new Error('No file selected');
      }

      setIsUploading(true);
      setFiles(files);
      const [file] = files;
      
      // Upload to Cloudinary via Django backend
      console.log('📤 Uploading image to Cloudinary...');
      const result = await uploadFile(file, 'flow_generator/images');
      
      updateNodeData(id, {
        content: {
          url: result.url, // Permanent Cloudinary URL
          type: file.type,
        },
      });
      
      console.log('✅ IMAGE UPLOADED TO CLOUDINARY:', {
        nodeId: id,
        fileName: file.name,
        cloudinaryUrl: result.url,
        fileSize: file.size,
      });
    } catch (error) {
      handleError('Error uploading image', error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <NodeLayout id={id} data={data} type={type} title={title}>
      {isUploading && (
        <Skeleton className="flex aspect-video w-full animate-pulse items-center justify-center">
          <Loader2Icon
            size={16}
            className="size-4 animate-spin text-muted-foreground"
          />
        </Skeleton>
      )}
      {!isUploading && data.content && (
        <Image
          src={data.content.url}
          alt="Image"
          width={data.width ?? 1000}
          height={data.height ?? 1000}
          className="h-auto w-full"
        />
      )}
      {!isUploading && !data.content && (
        <Dropzone
          maxSize={1024 * 1024 * 10}
          minSize={1024}
          maxFiles={1}
          multiple={false}
          accept={{
            'image/*': [],
          }}
          onDrop={handleDrop}
          src={files}
          onError={console.error}
          className="rounded-none border-none bg-transparent p-0 shadow-none hover:bg-transparent dark:bg-transparent dark:hover:bg-transparent"
        >
          <DropzoneEmptyState className="p-4" />
          <DropzoneContent />
        </Dropzone>
      )}
    </NodeLayout>
  );
};

