// src/App.js
import React, { useState } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import Navigation from './components/Navigation';
import TournamentMatched from './components/TournamentMatches';

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
        <Navigation darkMode={darkMode} onToggleDarkMode={handleToggle} />
      </Router>
    </ThemeProvider>
  );
}

export default App;
