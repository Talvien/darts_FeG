// src/App.jsx
import React, { useState } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import Navigation from './assets/Navigation';

function App() {
  const [darkMode, setDarkMode] = useState(false);

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
    },
  });

  const handleToggle = () => {
    setDarkMode((prevMode) => !prevMode);
  };

  return (
    <ThemeProvider theme={theme}>
      <Router>
        <CssBaseline /> {/* Normalize styles */}
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
          <Navigation darkMode={darkMode} onToggleDarkMode={handleToggle} />
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;


