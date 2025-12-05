'use client';

import { cn } from '@/lib/utils';
import { memo } from 'react';
import type { HTMLAttributes } from 'react';
import ReactMarkdown, { type Options } from 'react-markdown';
import remarkGfm from 'remark-gfm';

export type AIResponseProps = HTMLAttributes<HTMLDivElement> & {
  options?: Options;
  children: Options['children'];
};

const components: Options['components'] = {
  ol: ({ node, children, className, ...props }) => (
    <ol className={cn('ml-4 list-outside list-decimal', className)} {...props}>
      {children}
    </ol>
  ),
  li: ({ node, children, className, ...props }) => (
    <li className={cn('py-1', className)} {...props}>
      {children}
    </li>
  ),
  ul: ({ node, children, className, ...props }) => (
    <ul className={cn('ml-4 list-outside list-disc', className)} {...props}>
      {children}
    </ul>
  ),
  strong: ({ node, children, className, ...props }) => (
    <span className={cn('font-semibold', className)} {...props}>
      {children}
    </span>
  ),
  a: ({ node, children, className, ...props }) => (
    <a
      className={cn('font-medium text-primary underline', className)}
      target="_blank"
      rel="noreferrer"
      {...props}
    >
      {children}
    </a>
  ),
  h1: ({ node, children, className, ...props }) => (
    <h1
      className={cn('mt-6 mb-2 font-semibold text-3xl', className)}
      {...props}
    >
      {children}
    </h1>
  ),
  h2: ({ node, children, className, ...props }) => (
    <h2
      className={cn('mt-6 mb-2 font-semibold text-2xl', className)}
      {...props}
    >
      {children}
    </h2>
  ),
  h3: ({ node, children, className, ...props }) => (
    <h3 className={cn('mt-6 mb-2 font-semibold text-xl', className)} {...props}>
      {children}
    </h3>
  ),
  h4: ({ node, children, className, ...props }) => (
    <h4 className={cn('mt-6 mb-2 font-semibold text-lg', className)} {...props}>
      {children}
    </h4>
  ),
  h5: ({ node, children, className, ...props }) => (
    <h5
      className={cn('mt-6 mb-2 font-semibold text-base', className)}
      {...props}
    >
      {children}
    </h5>
  ),
  h6: ({ node, children, className, ...props }) => (
    <h6 className={cn('mt-6 mb-2 font-semibold text-sm', className)} {...props}>
      {children}
    </h6>
  ),
  pre: ({ node, className, children }) => (
    <pre
      className={cn(
        'my-4 overflow-x-auto rounded-lg bg-zinc-900 p-4 text-sm text-zinc-100',
        className
      )}
    >
      {children}
    </pre>
  ),
  code: ({ node, className, children, ...props }) => {
    const isInline = !className?.includes('language-');
    if (isInline) {
      return (
        <code
          className="rounded bg-zinc-800 px-1.5 py-0.5 text-sm text-zinc-200"
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <code className={cn('block', className)} {...props}>
        {children}
      </code>
    );
  },
};

export const AIResponse = memo(
  ({ className, options, children, ...props }: AIResponseProps) => (
    <div
      className={cn(
        'size-full [&>*:first-child]:mt-0 [&>*:last-child]:mb-0',
        className
      )}
      {...props}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
        {...options}
      >
        {children}
      </ReactMarkdown>
    </div>
  ),
  (prevProps, nextProps) => prevProps.children === nextProps.children
);
