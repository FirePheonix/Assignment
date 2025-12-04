"use client";

import { motion } from "motion/react";
import type { FC } from "react";
import Image from "next/image";

export interface Message {
  id: string;
  name: string;
  message: string;
  timestamp?: string;
}

interface ChatMessageProps {
  message: Message;
  isCurrentUser: boolean;
  avatar: string;
}

const ChatMessage: FC<ChatMessageProps> = ({
  message,
  isCurrentUser,
  avatar,
}) => {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.4 }}
      className={`flex mb-4 ${
        isCurrentUser ? "justify-end" : "justify-start"
      } items-end`}
    >
      {!isCurrentUser && (
        <div className="flex-shrink-0 mr-2">
          <div className="w-8 h-8 rounded-full overflow-hidden">
            <Image
              src={avatar || "/placeholder.svg"}
              alt={`${message.name}'s avatar`}
              width={32}
              height={32}
              className="object-cover"
            />
          </div>
        </div>
      )}

      <div
        className={`max-w-[70%] px-2 py-1 rounded-2xl ${
          isCurrentUser
            ? "bg-blue-500 text-white rounded-br-none"
            : "bg-gray-200 text-black rounded-bl-none"
        }`}
      >
        <p className="text-sm sm:text-base">{message.message}</p>
        {message.timestamp && (
          <p
            className={`text-xs mt-1 ${
              isCurrentUser ? "text-blue-100" : "text-gray-500"
            }`}
          >
            {message.timestamp}
          </p>
        )}
      </div>

      {isCurrentUser && <div className="w-8 "></div>}
    </motion.div>
  );
};

export default ChatMessage;
