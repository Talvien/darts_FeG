import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  ListItemText,
  Checkbox,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import * as Yup from 'yup';
import { useFormik } from 'formik';
import { useNavigate } from 'react-router-dom'; // Import useNavigate for navigation

const Tournament = () => {
  const [players, setPlayers] = useState([]);
  const [selectedPlayers, setSelectedPlayers] = useState([]);
  const [tournamentFormats, setTournamentFormats] = useState([]);
  const navigate = useNavigate(); // Initialize useNavigate for navigation

  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const response = await fetch('/api/players');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const playersData = await response.json();
        setPlayers(playersData);
      } catch (error) {
        console.error('Error fetching players:', error);
      }
    };

    const fetchTournamentFormats = async () => {
      try {
        const response = await fetch('/api/tournament-formats');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const formatsData = await response.json();
        setTournamentFormats(formatsData);
      } catch (error) {
        console.error('Error fetching tournament formats:', error);
      }
    };

    fetchTournamentFormats();
    fetchPlayers();
  }, []);

  const handlePlayerToggle = (playerId) => {
    const currentIndex = selectedPlayers.indexOf(playerId);
    const newSelectedPlayers = [...selectedPlayers];

    if (currentIndex === -1) {
      newSelectedPlayers.push(playerId);
    } else {
      newSelectedPlayers.splice(currentIndex, 1);
    }

    setSelectedPlayers(newSelectedPlayers);
  };

  const formik = useFormik({
    initialValues: {
      tournamentName: '',
      newPlayerName: '',
      selectedFormat: '',
      numberOfGroups: 'Auto',
    },
    validationSchema: Yup.object({
      tournamentName: Yup.string().required('Tournament Name is required'),
      selectedFormat: Yup.string().required('Tournament Format is required'),
      numberOfGroups: Yup.string().required('Number of Groups is required'),
    }),
    onSubmit: async (values, { resetForm }) => {
      if (!values.tournamentName || selectedPlayers.length < 2) {
        alert('Bitte Turniernamen eingeben und mindestens zwei Spieler auswählen.');
        return;
      }

      const newTournament = {
        name: values.tournamentName,
        format_id: values.selectedFormat,
        players: selectedPlayers,
        groups: values.numberOfGroups,
      };

      try {
        const response = await fetch('/api/create-tournament', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(newTournament),
        });

        if (!response.ok) {
          throw new Error('Failed to create tournament');
        }

        const createdTournament = await response.json();
        console.log('Tournament created:', createdTournament); // Add log here

        resetForm();
        setSelectedPlayers([]);
        navigate(`/tournaments/${createdTournament.tournament_id}`); // Navigate to the matches screen
      } catch (error) {
        console.error('Error creating tournament:', error);
      }
    },
  });

  async function handleCreatePlayer() {
    if (formik.values.newPlayerName.trim() === '') return;

    const newPlayer = { name: formik.values.newPlayerName };
    try {
      const response = await fetch('/api/players', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newPlayer),
      });

      if (!response.ok) {
        throw new Error('Failed to add player');
      }

      const addedPlayer = await response.json();
      console.log('Player created:', addedPlayer); // Add log here
      setPlayers((prevPlayers) => [...prevPlayers, addedPlayer]);
      formik.setFieldValue('newPlayerName', '');
    } catch (error) {
      console.error('Error creating player:', error);
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Neues Turnier erstellen
      </Typography>

      <form onSubmit={formik.handleSubmit}>
        {/* Tournament Name Input Field */}
        <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
          <TextField
            label="Turnier Name"
            variant="outlined"
            name="tournamentName"
            value={formik.values.tournamentName}
            onChange={formik.handleChange}
            error={formik.touched.tournamentName && Boolean(formik.errors.tournamentName)}
            helperText={formik.touched.tournamentName && formik.errors.tournamentName}
          />
        </FormControl>
        
        {/* Tournament Format Selection and Number of Groups */}
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <FormControl fullWidth variant="outlined">
            <InputLabel id="tournament-format-label">Turnierformat</InputLabel>
            <Select
              labelId="tournament-format-label"
              name="selectedFormat"
              value={formik.values.selectedFormat}
              onChange={formik.handleChange}
              label="Turnierformat"
              error={formik.touched.selectedFormat && Boolean(formik.errors.selectedFormat)}
            >
              {tournamentFormats.map((format) => (
                <MenuItem key={format.format_id} value={format.format_id}>
                  {format.format_name}
                </MenuItem>
              ))}
            </Select>
            {formik.touched.selectedFormat && formik.errors.selectedFormat && (
              <Typography variant="caption" color="error">{formik.errors.selectedFormat}</Typography>
            )}
          </FormControl>

          <FormControl fullWidth variant="outlined">
            <InputLabel id="number-of-groups-label">Gruppenanzahl</InputLabel>
            <Select
              labelId="number-of-groups-label"
              name="numberOfGroups"
              value={formik.values.numberOfGroups}
              onChange={formik.handleChange}
              label="Gruppenanzahl"
              error={formik.touched.numberOfGroups && Boolean(formik.errors.numberOfGroups)}
            >
              <MenuItem value="Auto">Auto</MenuItem>
              <MenuItem value="1">1</MenuItem>
              <MenuItem value="2">2</MenuItem>
              <MenuItem value="3">3</MenuItem>
            </Select>
            {formik.touched.numberOfGroups && formik.errors.numberOfGroups && (
              <Typography variant="caption" color="error">{formik.errors.numberOfGroups}</Typography>
            )}
          </FormControl>
        </Box>

        {/* Player Selection List */}
        <Typography variant="h6">Spieler auswählen</Typography>
        <Box
          sx={{
            maxHeight: 300,
            overflowY: 'auto',
            mb: 2,
            border: '1px solid #ccc',
            borderRadius: '4px',
            padding: 1,
          }}
        >
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: 2,
              margin: 2,
              maxHeight: 400,
              overflowY: 'auto',
              '&::-webkit-scrollbar': {
                display: 'none',
              },
            }}
          >
            {players.map((player) => (
              <Box
                key={player.player_id}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Checkbox
                  edge="start"
                  checked={selectedPlayers.indexOf(player.player_id) !== -1}
                  tabIndex={-1}
                  disableRipple
                  onClick={() => handlePlayerToggle(player.player_id)}
                />
                <ListItemText primary={player.name} />
              </Box>
            ))}
          </Box>
        </Box>

        <Typography variant="h6">Neuen Spieler erstellen</Typography>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
            <TextField
              label="Spielername"
              variant="outlined"
              name="newPlayerName"
              value={formik.values.newPlayerName}
              onChange={formik.handleChange}
              error={formik.touched.newPlayerName && Boolean(formik.errors.newPlayerName)}
              helperText={formik.touched.newPlayerName && formik.errors.newPlayerName}
              slotProps={{
                input: {
                  sx: {
                    height: 50,
                  },
                },
              }}
            />
          </FormControl>

          {/* New Player Creation Button */}
          <Button
            variant="contained"
            color="primary"
            onClick={handleCreatePlayer}
            sx={{
              mb: 2,
              height: 50,
              minWidth: 200,
            }}
          >
            Add Player
          </Button>
        </Box>

        {/* Tournament Creation Button */}
        <Box sx={{ mt: 2 }}>
          <Button variant="contained" color="secondary" type="submit">
            Create Tournament
          </Button>
        </Box>
      </form>
    </Box>
  );
};

export default Tournament;
