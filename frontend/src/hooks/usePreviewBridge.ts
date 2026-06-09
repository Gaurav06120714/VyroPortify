"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface Options {
  targetOrigin: string;
  iframeRef: React.RefObject<HTMLIFrameElement | null>;
  readyTimeoutMs?: number;
}

interface UsePreviewBridgeResult {
  ready: boolean;
  push: (payload: unknown) => void;
}

export function usePreviewBridge({
  targetOrigin,
  iframeRef,
  readyTimeoutMs = 4000,
}: Options): UsePreviewBridgeResult {
  
  const [ready, setReady] = useState(false);
  const readyRef = useRef(false);
  const queuedRef = useRef<unknown[]>([]);

  useEffect(() => {
    const onMessage = (e: MessageEvent) => {
      
      if (targetOrigin !== "*" && e.origin !== targetOrigin) return;
      const data = e.data as { type?: string; message?: string } | undefined;
      if (!data || typeof data.type !== "string") return;

      if (data.type === "vyro:preview:ready") {
        readyRef.current = true;
        setReady(true);
        
        const iframe = iframeRef.current;
        if (iframe?.contentWindow) {
          for (const payload of queuedRef.current) {
            iframe.contentWindow.postMessage(
              { type: "vyro:preview:update", payload },
              targetOrigin,
            );
          }
          queuedRef.current = [];
        }
      } else if (data.type === "vyro:preview:error") {
        
        console.warn("preview_bridge_iframe_error", data.message);
      }
    };

    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [targetOrigin, iframeRef]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (!readyRef.current) {
        console.info(
          "preview_bridge_no_handshake — falling back to iframe key-reload model",
        );
      }
    }, readyTimeoutMs);
    return () => clearTimeout(timer);
  }, [readyTimeoutMs]);

  const push = useCallback(
    (payload: unknown) => {
      const iframe = iframeRef.current;
      if (!readyRef.current || !iframe?.contentWindow) {
        
        queuedRef.current.push(payload);
        return;
      }
      iframe.contentWindow.postMessage(
        { type: "vyro:preview:update", payload },
        targetOrigin,
      );
    },
    [targetOrigin, iframeRef],
  );

  return { ready, push };
}
