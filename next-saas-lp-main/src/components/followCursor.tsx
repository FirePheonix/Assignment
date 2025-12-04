"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";

export interface FollowCursorProps {
  /**
   * Color of the blob cursor
   * @default "#6ECE9D"
   */
  color?: string;

  /**
   * Number of blobs to render
   * @default 3
   */
  blobCount?: number;

  /**
   * Array of blob sizes in pixels
   * @default [60, 125, 75]
   */
  blobSizes?: number[];

  /**
   * Animation duration for blob movement
   * @default 0.5
   */
  duration?: number;

  /**
   * Animation ease function
   * @default "power2.out"
   */
  ease?: string;

  /**
   * Whether to enable on mobile devices
   * @default false
   */
  enableMobile?: boolean;
}

const FollowCursor = ({
  color = "#6ECE9D",
  blobCount = 3,
  blobSizes = [60, 125, 75],
  duration = 0.5,
  ease = "power2.out",
  enableMobile = false,
}: FollowCursorProps) => {
  const cursorRef = useRef<HTMLDivElement>(null);
  const blobRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);

    // Check if device is mobile
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    if (isMobile && !enableMobile) return;

    const handleMouseMove = (e: MouseEvent) => {
      const { clientX, clientY } = e;

      blobRefs.current.forEach((blob, index) => {
        if (blob) {
          const size = blobSizes[index] || 75;
          gsap.to(blob, {
            x: clientX - size / 2,
            y: clientY - size / 2,
            duration: duration + index * 0.1,
            ease: ease,
          });
        }
      });
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, [duration, ease, enableMobile, blobSizes]);

  if (!isMounted) return null;

  // Check if mobile and not enabled
  if (typeof window !== "undefined") {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    if (isMobile && !enableMobile) return null;
  }

  return (
    <>
      <div
        className="pointer-events-none fixed inset-0 overflow-hidden select-none"
        style={{
          zIndex: 9999,
        }}
      >
        {Array.from({ length: blobCount }).map((_, index) => (
          <div
            key={index}
            ref={(el) => {
              blobRefs.current[index] = el;
            }}
            className="absolute rounded-full"
            style={{
              width: `${blobSizes[index] || 75}px`,
              height: `${blobSizes[index] || 75}px`,
              backgroundColor: color,
              filter: "url(#gooey)",
              opacity: 0.8,
              top: 0,
              left: 0,
            }}
          />
        ))}
      </div>

      <svg
        xmlns="http://www.w3.org/2000/svg"
        version="1.1"
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: 0,
          height: 0,
          pointerEvents: "none",
        }}
      >
        <defs>
          <filter id="gooey">
            <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
            <feColorMatrix
              in="blur"
              mode="matrix"
              values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7"
              result="gooey"
            />
            <feComposite in="SourceGraphic" in2="gooey" operator="atop" />
          </filter>
        </defs>
      </svg>
    </>
  );
};

export default FollowCursor;