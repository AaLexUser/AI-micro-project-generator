"use client";
import { FormEvent, useState } from "react";
import { toast } from "sonner";

export function NewsletterSignup() {
  const [email, setEmail] = useState("");

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim()) {
      toast.message("Please enter your email");
      return;
    }
    toast.success("Subscribed");
    setEmail("");
  }

  return (
    <form className="flex gap-2" onSubmit={onSubmit}>
      <input
        className="w-full rounded-md border bg-background/80 px-3 py-2 text-sm backdrop-blur-sm"
        placeholder="Enter your email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        type="email"
        required
      />
      <button className="rounded-md bg-primary px-3 py-2 text-xs text-primary-foreground" type="submit">
        Subscribe
      </button>
    </form>
  );
}





