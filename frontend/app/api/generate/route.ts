import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";

  const res = await fetch(`${backendUrl}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      issue: body.issue,
      presets: body.presets ?? null,
      config_path: body.config_path ?? null,
      config_overrides: body.config_overrides ?? null,
    }),
  });

  if (!res.ok) {
    return NextResponse.json({ error: await res.text() }, { status: res.status });
  }
  const data = await res.json();
  return NextResponse.json(data);
}


