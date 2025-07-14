import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Box, Typography, Paper, Chip, TextField, Button } from '@mui/material';
import { ReadyState } from 'react-use-websocket';

export default function Dashboard({ data, status }) {
  const statusMap = {
    [ReadyState.CONNECTING]: 'Connecting',
    [ReadyState.OPEN]: 'Connected',
    [ReadyState.CLOSING]: 'Closing',
    [ReadyState.CLOSED]: 'Closed',
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated'
  };

  // Strategy config state
  const [fast, setFast] = useState(8);
  const [slow, setSlow] = useState(24);
  const [leverage, setLeverage] = useState(1);

  // Load config on mount
  useEffect(() => {
    axios.get('/api/strategy')
      .then(res => {
        setFast(res.data.fast);
        setSlow(res.data.slow);
        setLeverage(res.data.leverage);
      })
      .catch(err => console.error('Error loading strategy config', err));
  }, []);

  const handleSave = () => {
    axios.post('/api/strategy', { fast, slow, leverage })
      .then(res => console.log('Config saved:', res.data))
      .catch(err => console.error('Error saving config', err));
  };

  return (
    <Box>
      <Paper sx={{ p:2, mb:2 }}>
        <Typography variant="h6">
          WebSocket Status: <Chip label={statusMap[status]} color={status === ReadyState.OPEN ? 'success' : 'default'} />
        </Typography>
      </Paper>

      <Paper sx={{ p:2, mb:2 }}>
        <Typography variant="h6">Latest Update</Typography>
        {data ? <pre>{JSON.stringify(data, null, 2)}</pre> : <Typography>No data yet...</Typography>}
      </Paper>

      <Paper sx={{ p:2, mb:2 }}>
        <Typography variant="h6">Strategy Configuration</Typography>
        <Box component="form" sx={{ display: 'flex', gap:2, alignItems:'center', mt:2 }}>
          <TextField
            label="EMA Fast"
            type="number"
            value={fast}
            onChange={e => setFast(Number(e.target.value))}
            size="small"
          />
          <TextField
            label="EMA Slow"
            type="number"
            value={slow}
            onChange={e => setSlow(Number(e.target.value))}
            size="small"
          />
          <TextField
            label="Leverage (1=long/cross, -1=short)"
            type="number"
            value={leverage}
            onChange={e => setLeverage(Number(e.target.value))}
            size="small"
          />
          <Button variant="contained" onClick={handleSave}>Save</Button>
        </Box>
      </Paper>
    </Box>
  );
}
