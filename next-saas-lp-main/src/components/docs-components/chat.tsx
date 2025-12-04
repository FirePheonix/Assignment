"use client";

import { type FC, useRef, useEffect, useState, useLayoutEffect } from "react";
import { motion, AnimatePresence, useInView } from "motion/react";
import ChatMessage, { type Message } from "./chat-message";

export interface User {
  name: string;
  avatar: string;
}

interface ChatProps {
  messages: Message[];
  currentUser: string;
  users: User[];
}

const Chat: FC<ChatProps> = ({ messages, currentUser, users }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [visibleMessages, setVisibleMessages] = useState<Message[]>([]);
  const isInView = useInView(containerRef, { once: true, amount: 0.3 });

  useEffect(() => {
    if (messages.length === 0 || !isInView) return;

    setVisibleMessages([]);
    let cancelled = false;

    (async () => {
      for (const msg of messages) {
        if (cancelled) return; // guard before delay
        await new Promise((r) => setTimeout(r, 700));
        if (cancelled) return; // guard after delay
        setVisibleMessages((prev) => [...prev, msg]);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [messages, isInView]);

  useLayoutEffect(() => {
    const el = containerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [visibleMessages]);

  const getUserAvatar = (name: string) =>
    users.find((u) => u.name === name)?.avatar ??
    "/placeholder.svg?height=40&width=40";

  return (
    <div
      ref={containerRef}
      className="w-full h-full overflow-y-auto p-2 bg-white dark:bg-[#212121] flex flex-col py-[2rem]"
    >
      <AnimatePresence initial={false} mode="popLayout">
        {visibleMessages.map((message) => (
          <motion.div
            key={message.id}
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.4 }}
            className={`flex mb-4 ${
              message.name === currentUser ? "justify-end" : "justify-start"
            } items-end`}
          >
            <ChatMessage
              message={message}
              isCurrentUser={message.name === currentUser}
              avatar={getUserAvatar(message.name)}
            />
          </motion.div>
        ))}
      </AnimatePresence>

      {visibleMessages.length > 0 &&
        visibleMessages[visibleMessages.length - 1].name === currentUser && (
          <div className="text-xs text-right mt-1 mr-2 dark:text-white text-black">
            Delivered
          </div>
        )}
    </div>
  );
};

export default Chat;
