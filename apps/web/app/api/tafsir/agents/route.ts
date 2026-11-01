import { forwardBackendRequest } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export function GET() {
  return forwardBackendRequest("/api/v1/tafsir/agents");
}
