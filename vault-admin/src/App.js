import React from 'react';
import useLiveUpdates from './hooks/useLiveUpdates';
import Dashboard from './components/Dashboard';

function App() {
  const { lastJsonMessage, readyState } = useLiveUpdates();

  return (
    <div>
      <h1>Trading Desk Admin</h1>
      <Dashboard data={lastJsonMessage} status={readyState} />
    </div>
  );
}

export default App;
