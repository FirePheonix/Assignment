import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/flow-components/ui/select';
import { videoModels } from '@/lib/models/video';
import type { VideoModel } from '@/lib/models/video';

type VideoDurationSelectorProps = {
  value: number;
  modelId: VideoModel;
  onChange: (value: number) => void;
  className?: string;
};

const defaultDurations = [4, 8, 12, 16, 20];

export const VideoDurationSelector = ({
  value,
  modelId,
  onChange,
  className,
}: VideoDurationSelectorProps) => {
  const model = videoModels[modelId];
  const durations = model.durations || defaultDurations;

  return (
    <Select value={value.toString()} onValueChange={(v) => onChange(Number(v))}>
      <SelectTrigger className={className ?? 'rounded-md h-9'}>
        <SelectValue placeholder="Select duration" />
      </SelectTrigger>
      <SelectContent className="z-[1000]">
        {durations.map((duration) => (
          <SelectItem key={duration} value={duration.toString()}>
            {duration}s
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};
