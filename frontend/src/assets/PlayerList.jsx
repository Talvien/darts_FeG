import React, { useEffect, useState } from 'react';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';

function PlayerList() {
  const [players, setPlayers] = useState([]);
  const [error, setError] = useState(null);
  const [newPlayerName, setNewPlayerName] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');

  useEffect(() => {
    async function fetchPlayers() {
      try {
        const response = await fetch('/api/players');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const playersData = await response.json();
        setPlayers(playersData);
      } catch (error) {
        setError(error.message);
      }
    }

    fetchPlayers();
  }, []);

  const handleAddPlayer = async (e) => {
    e.preventDefault(); // Prevent the default form submission

    const newPlayer = { name: newPlayerName }; // Ensure the key matches the JSON structure
    try {
      const response = await fetch('/api/players', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json', // Ensure this is set correctly
        },
        body: JSON.stringify(newPlayer), // Convert the new player object to JSON
      });

      if (!response.ok) {
        throw new Error('Failed to add player');
      }

      const addedPlayer = await response.json();
      setPlayers((prevPlayers) => [...prevPlayers, addedPlayer]); // Update the player list
      setNewPlayerName(''); // Clear the input field
    } catch (error) {
      setError(error.message);
    }
  };

  const handleSelectChange = (event) => {
    setSelectedPlayer(event.target.value); // Update the selected player
  };

  const handleDeletePlayer = async () => {
    if (!selectedPlayer) {
      setError('Please select a player to delete.');
      return;
    }

    try {
      const response = await fetch(`/api/players/${selectedPlayer}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete player');
      }

      setPlayers((prevPlayers) => prevPlayers.filter(player => player.player_id !== selectedPlayer));
      setSelectedPlayer(''); // Clear the selected player
      setError(''); // Clear any error messages
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <div>
      <h2>Spielerliste</h2>
      {error && <p>Error: {error}</p>}
      
      <FormControl fullWidth variant="outlined" style={{ marginBottom: '20px' }}>
        <InputLabel id="select-player-label">Spieler auswählen</InputLabel>
        <Select
          labelId="select-player-label"
          value={selectedPlayer}
          onChange={handleSelectChange}
          label="Spieler auswählen"
        >
          {players.map(player => (
            <MenuItem key={player.player_id} value={player.player_id}>
              {player.name} {/* Display player name */}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Button 
        variant="contained" 
        color="secondary" 
        onClick={handleDeletePlayer}
        style={{ marginBottom: '20px' }} // Add margin to separate from form
      >
        Spieler löschen
      </Button>

      <form onSubmit={handleAddPlayer}>
        <TextField
          label="Spielername"
          variant="outlined"
          value={newPlayerName}
          onChange={(e) => setNewPlayerName(e.target.value)}
          required
          fullWidth
        />
        <Button 
          variant="contained" 
          color="primary" 
          type="submit"
          style={{ marginTop: '10px' }}
        >
          Spieler hinzufügen
        </Button>
      </form>
    </div>
  );
}

export default PlayerList;
