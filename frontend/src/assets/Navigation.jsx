// src/components/Navigation.js
import React, { useState } from 'react';
import { AppBar, Tabs, Tab, Toolbar, Typography, Switch, Container } from '@mui/material';
import { Link, Routes, Route } from 'react-router-dom';
import PlayerList from './PlayerList'; // Import your PlayerList component
import Tournament from './Tournament'; // Import your Tournament component
import TournamentRound from './TournamentRound';
import TournamentWinner from './TournamentWinner'

function Navigation({ darkMode, onToggleDarkMode }) {
  const [value, setValue] = useState(0); // State for the selected tab

  const handleTabChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Tabs
            value={value}
            onChange={handleTabChange}
            sx={{ flexGrow: 1 }} // Make Tabs grow to fill available space
          >
            <Tab
              label="Turnier"
              component={Link}
              to="/"
              sx={{
                color: value === 0 ? 'yellow' : 'inherit', // Change color for selected tab
                '&.Mui-selected': {
                  color: 'yellow', // Ensure selected tab color is visible
                },
              }}
            />
            <Tab
              label="Spieler Verwaltung"
              component={Link}
              to="/player-management"
              sx={{
                color: value === 1 ? 'yellow' : 'inherit',
                '&.Mui-selected': {
                  color: 'yellow',
                },
              }}
            />
          </Tabs>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            FeG Darts Turnier Maker
          </Typography>
          <Switch checked={darkMode} onChange={onToggleDarkMode} />
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" style={{ marginTop: '20px' }}>
        <Routes>
          <Route path="/" element={<Tournament />} /> {/* Set Tournament as the starting page */}
          <Route path="/tournaments/:tournamentId" element={<TournamentRound />} />
          <Route path="/tournaments/:tournamentId/winner" element={<TournamentWinner />} />
          <Route path="/player-management" element={<PlayerList />} />
        </Routes>
      </Container>
    </>
  );
}

export default Navigation;
