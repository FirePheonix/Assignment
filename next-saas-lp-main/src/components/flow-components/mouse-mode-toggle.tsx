'use client';

import { MousePointer2, Hand } from 'lucide-react';
import { useMouseMode } from './controls';

export const MouseModeToggle = () => {
  const { mouseMode, setMouseMode } = useMouseMode();

  return (
    <div className="absolute left-4 top-1/2 -translate-y-1/2 z-[60]">
      <div className="bg-black border border-gray-700/50 rounded-2xl p-1 shadow-lg backdrop-blur-sm">
        <div className="relative flex flex-col w-8 h-16">
          {/* Switch Track */}
          <div className="absolute inset-1 rounded-xl bg-gray-800/50" />
          
          {/* Switch Slider */}
          <div 
            className={`absolute w-6 h-6 rounded-lg bg-blue-600 shadow-lg transition-transform duration-300 z-10 ${
              mouseMode === 'select' ? 'top-1 left-1' : 'bottom-1 left-1'
            }`}
          />
          
          {/* Select Mode Icon */}
          <div 
            className={`relative z-20 w-6 h-6 rounded-lg flex items-center justify-center cursor-pointer transition-colors duration-300 mt-1 ml-1 ${
              mouseMode === 'select' ? 'text-white' : 'text-gray-500'
            }`}
            onClick={() => setMouseMode('select')}
            title="Selection Mode"
          >
            <MousePointer2 className="h-3.5 w-3.5" />
          </div>
          
          {/* Pan Mode Icon */}
          <div 
            className={`relative z-20 w-6 h-6 rounded-lg flex items-center justify-center cursor-pointer transition-colors duration-300 mb-1 ml-1 ${
              mouseMode === 'pan' ? 'text-white' : 'text-gray-500'
            }`}
            onClick={() => setMouseMode('pan')}
            title="Pan Mode"
          >
            <Hand className="h-3.5 w-3.5" />
          </div>
        </div>
      </div>
    </div>
  );
};