// vault-admin/src/hooks/useLiveUpdates.js
import useWebSocket, { ReadyState } from 'react-use-websocket';

export default function useLiveUpdates() {
  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket('ws://localhost:8000/ws', {
    retryOnError: true,
    reconnectInterval: 3000,
  });

  return { lastJsonMessage, readyState };
}