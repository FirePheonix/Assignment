import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/flow-components/ui/select';
import { videoModels } from '@/lib/models/video';
import type { VideoModel } from '@/lib/models/video';

type VideoSizeSelectorProps = {
  value: string;
  modelId: VideoModel;
  onChange: (value: string) => void;
  className?: string;
};

const defaultSizes = ['1280x720', '1920x1080', '1080x1920', '720x1280'];

export const VideoSizeSelector = ({
  value,
  modelId,
  onChange,
  className,
}: VideoSizeSelectorProps) => {
  const model = videoModels[modelId];
  const sizes = model.sizes || defaultSizes;

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className={className ?? 'rounded-md h-9'}>
        <SelectValue placeholder="Select size" />
      </SelectTrigger>
      <SelectContent className="z-[1000]">
        {sizes.map((size) => (
          <SelectItem key={size} value={size}>
            {size}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};
