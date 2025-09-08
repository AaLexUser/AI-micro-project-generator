import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  try {
    const res = await fetch(`${backendUrl}/healthz`, { cache: "no-store" });
    if (!res.ok) throw new Error("Bad status");
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ status: "down" }, { status: 200 });
  }
}


