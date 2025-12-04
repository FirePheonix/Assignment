import { NodeToolbar as NodeToolbarRaw, useReactFlow } from '@xyflow/react';
import { Position } from '@xyflow/react';
import { Fragment, type ReactNode } from 'react';
import { Tooltip, TooltipContent, TooltipTrigger } from '../ui/tooltip';

type NodeToolbarProps = {
  id: string;
  items:
    | {
        tooltip?: string;
        children: ReactNode;
      }[]
    | undefined;
};

export const NodeToolbar = ({ id, items }: NodeToolbarProps) => {
  const { getNode } = useReactFlow();
  const node = getNode(id);

  return (
    <NodeToolbarRaw
      isVisible={node?.selected}
      position={Position.Bottom}
      className="flex items-center gap-2 rounded-lg bg-background/95 p-2 backdrop-blur-sm shadow-lg border border-border"
      style={{ zIndex: 1000 }}
    >
      {items?.map((button, index) =>
        button.tooltip ? (
          <Tooltip key={button.tooltip}>
            <TooltipTrigger asChild>{button.children}</TooltipTrigger>
            <TooltipContent side="top">{button.tooltip}</TooltipContent>
          </Tooltip>
        ) : (
          <Fragment key={index}>{button.children}</Fragment>
        )
      )}
    </NodeToolbarRaw>
  );
};

