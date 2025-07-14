import useWebSocket from 'react-use-websocket';

export default function useLiveUpdates() {
  const { lastJsonMessage: data, readyState } = useWebSocket('ws://localhost:8000/ws', {
    retryOnError: true,
    reconnectInterval: 3000,
  });

  return { data, readyState };
}
