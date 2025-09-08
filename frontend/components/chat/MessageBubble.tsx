"use client";
import type { FC } from "react";
import clsx from "clsx";
import { User, Bot } from "lucide-react";

export type MessageBubbleProps = {
  role: "user" | "assistant";
  content: string;
};

export const MessageBubble: FC<MessageBubbleProps> = ({ role, content }) => {
  const isUser = role === "user";
  return (
    <div
      className={clsx(
        "flex gap-3 rounded-2xl p-3",
        "glass ring-gradient border",
        isUser ? "bg-blue-50/60" : "bg-muted/60",
      )}
    >
      <div className={clsx(
        "mt-1 flex h-8 w-8 items-center justify-center rounded-full shadow-sm",
        isUser ? "bg-blue-100 text-blue-700" : "bg-gray-200 text-gray-700"
      )}>
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">{role}</div>
        <div className="whitespace-pre-wrap text-sm leading-relaxed">{content}</div>
      </div>
    </div>
  );
};


