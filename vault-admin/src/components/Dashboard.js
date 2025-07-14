import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

export default function Dashboard({ data, status }) {
  return (
    <Box p={2}>
      <Paper elevation={3} sx={{ p:2, mb:2 }}>
        <Typography>WebSocket Status: {status === 1 ? 'Connected' : 'Disconnected'}</Typography>
      </Paper>
      {data && (
        <Paper elevation={3} sx={{ p:2 }}>
          <Typography>Latest Update:</Typography>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </Paper>
      )}
    </Box>
  );
}
