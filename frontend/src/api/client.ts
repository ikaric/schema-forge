import type { State } from "./types";

export async function fetchState(): Promise<State> {
  const res = await fetch("/api/state");
  if (!res.ok) throw new Error(`/api/state ${res.status}`);
  return (await res.json()) as State;
}

export function artifactUrl(relPath: string): string {
  return `/api/artifacts/${relPath}`;
}

/**
 * Subscribe to live state pushes over the WebSocket, auto-reconnecting.
 * Returns a disconnect function.
 */
export function connectLiveState(
  onState: (state: State) => void,
  onConnected: (connected: boolean) => void,
): () => void {
  let socket: WebSocket | null = null;
  let closedByUs = false;
  let retry: ReturnType<typeof setTimeout> | undefined;

  const url = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;

  const open = () => {
    socket = new WebSocket(url);
    socket.onopen = () => onConnected(true);
    socket.onmessage = (event) => {
      try {
        onState(JSON.parse(event.data as string) as State);
      } catch {
        /* ignore malformed frame */
      }
    };
    socket.onclose = () => {
      onConnected(false);
      if (!closedByUs) retry = setTimeout(open, 1500);
    };
    socket.onerror = () => socket?.close();
  };
  open();

  return () => {
    closedByUs = true;
    if (retry) clearTimeout(retry);
    socket?.close();
  };
}
