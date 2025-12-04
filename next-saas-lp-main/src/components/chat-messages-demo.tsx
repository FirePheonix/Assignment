"use client";

import { useState } from "react";
import Chat, { type User } from "@/components/docs-components/chat";
import type { Message } from "@/components/docs-components/chat-message";
import IphoneFrame from "@/components/docs-components/iphone-frame";

export function ChatMessagesDemo() {
  // Define users with their avatars
  const users: User[] = [
    {
      name: "User1",
      avatar:
        "https://res.cloudinary.com/harshitproject/image/upload/v1746774430/member-five.png", // Replace with actual avatar URL
    },
    {
      name: "User2",
      avatar:
        "https://res.cloudinary.com/harshitproject/image/upload/v1746774430/member-four.png", // Replace with actual avatar URL
    },
  ];

  const [messages] = useState<Message[]>([
    {
      id: "m1",
      name: "User1",
      message: "Hey, why'd you call it Solace UI ?",
    },
    {
      id: "m2",
      name: "User2",
      message: "Because it is meant to be chill and stress free.",
    },
    {
      id: "m3",
      name: "User1",
      message: "So is it like a digital chill zone?",
    },
    {
      id: "m4",
      name: "User2",
      message: "Exactly, simple and calm design.",
    },
  ]);

  return (
    <main className="flex flex-col items-center justify-center p-4 ">
      {/* Clipping Wrapper */}
      <div className="mx-auto overflow-hidden w-[300px] h-[360px] sm:w-[350px] sm:h-[420px]">
        <IphoneFrame>
          <Chat
            messages={messages}
            currentUser="User2"
            users={users} // Pass the users array with avatars
          />
        </IphoneFrame>

        <div
          className="
        absolute bottom-0 left-0 right-0
        h-16 sm:h-20
        bg-gradient-to-b from-transparent
        to-white dark:to-[#212121]
        pointer-events-none
      "
          aria-hidden="true"
        ></div>
      </div>
    </main>
  );
}
