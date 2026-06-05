"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * postMessage bridge from the unified builder (parent window) to the preview
 * iframe. v1.7.4 substrate — used by the form refactor to push payload
 * updates without a full iframe reload.
 *
 * Protocol:
 *   parent → iframe:  { type: "vyro:preview:update", payload: <portfolio json> }
 *   iframe → parent:  { type: "vyro:preview:ready"  }   (handshake)
 *   iframe → parent:  { type: "vyro:preview:error", message }
 *
 * The iframe page is expected to listen for "vyro:preview:update" and
 * rerender from the payload without a fetch — same-origin in dev makes
 * this trivial; in prod the public viewer must opt-in by reading
 * window.parent.postMessage and trusting `window.parent.origin` against
 * an allowlist.
 *
 * If the iframe is cross-origin or fails to send the ready handshake
 * within {readyTimeoutMs}, the bridge logs and falls back to polling
 * (caller can use `lastUpdate` to trigger their own re-fetch loop).
 */
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
  // B8 fix: ready is now React state so consumers re-render on the
  // handshake. The previous version held it in a ref, which mutates
  // silently — components that conditionally rendered on `ready`
  // (e.g. a "Connecting…" placeholder) stayed stuck on `false`
  // forever even after the iframe acked. The ref is preserved for
  // the imperative event-handler path where we need a synchronous
  // read without waiting for state propagation.
  const [ready, setReady] = useState(false);
  const readyRef = useRef(false);
  const queuedRef = useRef<unknown[]>([]);

  // Listen for handshake + errors from the iframe.
  useEffect(() => {
    const onMessage = (e: MessageEvent) => {
      // Origin check — never trust a cross-origin sender.
      if (targetOrigin !== "*" && e.origin !== targetOrigin) return;
      const data = e.data as { type?: string; message?: string } | undefined;
      if (!data || typeof data.type !== "string") return;

      if (data.type === "vyro:preview:ready") {
        readyRef.current = true;
        setReady(true);
        // Flush anything queued before handshake.
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
        // Soft error — the iframe will keep its last good state.
        console.warn("preview_bridge_iframe_error", data.message);
      }
    };

    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [targetOrigin, iframeRef]);

  // If the handshake never arrives, mark ready=false and log; callers can
  // fall back to polling.
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
        // Queue until the iframe signals ready. Read from the ref
        // (synchronous) rather than `ready` state (stale-closure risk).
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
