import type { FC, ReactNode } from "react";
import {
  WifiIcon as LuWifi,
  BatteryMediumIcon as LuBatteryMedium,
  SignalIcon as LuSignal,
} from "lucide-react";

interface IphoneFrameProps {
  children: ReactNode;
  className?: string;
}

const IphoneFrame: FC<IphoneFrameProps> = ({ children, className = "" }) => {
  // Get current time in format HH:MM
  const getCurrentTime = () => {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, "0");
    const minutes = now.getMinutes().toString().padStart(2, "0");
    return `${hours}:${minutes}`;
  };

  return (
    // The main phone body
    <div
      className={`
        relative mx-auto
        border-[10px] border-gray-900 bg-[#212121]
        dark:border-gray-200 dark:bg-gray-100
        rounded-[44px]
        shadow-xl
        overflow-hidden
        w-[300px] h-[600px]
        sm:w-[350px] sm:h-[700px]
        ${className}
      `}
    >
      {/* Status Bar */}
      <div className="absolute top-0 left-0 right-0 h-8 z-20 px-6 flex justify-between items-center text-black dark:text-white dark:bg-[#212121] bg-white">
        {/* Left side - Time */}
        <div className="text-xs font-semibold flex items-center">
          <LuSignal className="w-3.5 h-3.5 mr-1" />
          {getCurrentTime()}
        </div>

        {/* Notch (center) */}
        <div
          className="
            absolute top-0 left-1/2 -translate-x-1/2
            w-[45%] h-[24px]
            bg-black dark:bg-gray-100
            rounded-b-xl
            z-30
            flex justify-center items-center space-x-2 p-1
          "
        >
          {/* Notch Details (Speaker/Camera) */}
          <div
            className="
            w-10 h-2 rounded-full
            bg-white dark:bg-black
          "
          ></div>
          <div
            className="
            w-2 h-2 rounded-full
            bg-white dark:bg-black
          "
          ></div>
        </div>

        {/* Right side - WiFi and Battery */}
        <div className="text-xs font-semibold flex items-center">
          <LuWifi className="w-4 h-4 mr-1" />
          <LuBatteryMedium className="w-5 h-5" />
        </div>
      </div>

      {/* The screen area */}
      <div
        className="
          w-full h-full
         (bg-white dark:bg-black)
          rounded-[34px] 
          overflow-hidden
          pt-8 
        "
      >
        {children}
      </div>

      {/* Side Buttons */}
      {/* Volume Up */}
      <div
        className="
        absolute -left-[12px] top-[100px] w-[4px] h-[50px] rounded-l-md

        bg-gray-800 dark:bg-gray-300
       
      "
      ></div>
      {/* Volume Down */}
      <div
        className="
        absolute -left-[12px] top-[160px] w-[4px] h-[50px] rounded-l-md
       
        bg-gray-800 dark:bg-gray-300
        
      "
      ></div>
      {/* Power/Side Button */}
      <div
        className="
        absolute -right-[12px] top-[130px] w-[4px] h-[80px] rounded-r-md
        
        bg-gray-800 dark:bg-gray-300
        
      "
      ></div>
    </div>
  );
};

export default IphoneFrame;
