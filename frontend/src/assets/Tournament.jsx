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
  const [groupStageFormats, setGroupStageFormats] = useState([]);
  const [knockOutStageFormats, setKnockOutStageFormats] = useState([]);
  const [defaultGroupStageFormat, setDefaultGroupStageFormat] = useState('');
  const [defaultKnockOutStageFormat, setDefaultKnockOutStageFormat] = useState('');
  const navigate = useNavigate(); // Initialize useNavigate for navigation
  const [error, setError] = useState('');
  const [numberOfGroupsOptions, setNumberOfGroupsOptions] = useState(['Auto', ...Array.from({ length: 3 }, (_, i) => (i + 1) * 2)]);

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

    const fetchGroupStageFormats = async () => {
      try {
        const response = await fetch('/api/group-stage-formats');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const formatsData = await response.json();
        setGroupStageFormats(formatsData);
        if (formatsData.length > 0) {
          formik.setFieldValue('groupStageFormat', formatsData[1].format_id); // Set initial value
        }
      } catch (error) {
        console.error('Error fetching group stage formats:', error);
      }
    };

    const fetchKnockOutStageFormats = async () => {
      try {
        const response = await fetch('/api/knock-out-stage-formats');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const formatsData = await response.json();
        setKnockOutStageFormats(formatsData);
        if (formatsData.length > 0) {
          formik.setFieldValue('knockOutStageFormat', formatsData[1].format_id); // Set initial value
        }
      } catch (error) {
        console.error('Error fetching knock-out stage formats:', error);
      }
    };

    fetchGroupStageFormats();
    fetchKnockOutStageFormats();
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
      groupStageFormat: '',
      knockOutStageFormat: '',
      numberOfGroups: 'Auto',
      advancingPlayers: 2,
    },
    validationSchema: Yup.object({
      tournamentName: Yup.string().required('Turniername erforderlich')
    }),
    onSubmit: async (values, { resetForm }) => {
      
      let numGroups = values.numberOfGroups;
      
      if (numGroups !== 'Auto') {
        numGroups = parseInt(numGroups, 10); // Convert to integer
      }
      if (!values.tournamentName || selectedPlayers.length < 2) {
        setError('Bitte Turniernamen eingeben und mindestens zwei Spieler auswählen.');
        return;
      }

      if (values.groupStageFormat !== '1' && values.numberOfGroups !== 'Auto' && selectedPlayers.length < values.numberOfGroups * 2) {
        setError('Die Anzahl der Gruppen darf nicht mehr als die Hälfte der ausgewählten Spieler betragen.');
        return;
      }

      const newTournament = {
        name: values.tournamentName,
        group_stage_format_id: values.groupStageFormat,
        knock_out_stage_format_id: values.knockOutStageFormat,
        players: selectedPlayers,
        num_groups: values.groupStageFormat === '1' ? null : numGroups,
        advancing_players: values.knockOutStageFormat === '1' ? null : values.advancingPlayers,
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
          setError(result.error); // Set the error message
          return;
        }

        const createdTournament = await response.json();
        console.log('Tournament created:', createdTournament); // Add log here

        resetForm();
        setSelectedPlayers([]);
        setError('');
        navigate(`/tournaments/${createdTournament.tournament_id}`); // Navigate to the matches screen
      } catch (error) {
        console.error('Error creating tournament:', error);
        setError('An error occurred while creating the tournament.');
      }
    },
  });

 
  formik.initialValues.groupStageFormat = defaultGroupStageFormat;
  formik.initialValues.knockOutStageFormat = defaultKnockOutStageFormat;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
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
            <InputLabel id="group-stage-format-label">Gruppenformat</InputLabel>
            <Select
              labelId="group-stage-format-label"
              name="groupStageFormat"
              value={formik.values.groupStageFormat}
              onChange={formik.handleChange}
              label="Group-Stage Format"
              error={formik.touched.groupStageFormat && Boolean(formik.errors.groupStageFormat)}
            >
              {groupStageFormats.map((format) => (
                <MenuItem key={format.format_id} value={format.format_id}>
                  {format.format_name}
                </MenuItem>
              ))}
            </Select>
            {formik.touched.groupStageFormat && formik.errors.groupStageFormat && (
              <Typography variant="caption" color="error">{formik.errors.groupStageFormat}</Typography>
            )}
          </FormControl>

          <FormControl fullWidth variant="outlined">
            <InputLabel id="knock-out-stage-format-label">Knock-Out Format</InputLabel>
            <Select
              labelId="knock-out-stage-format-label"
              name="knockOutStageFormat"
              value={formik.values.knockOutStageFormat}
              onChange={formik.handleChange}
              label="Knock-Out Stage Format"
              error={formik.touched.knockOutStageFormat && Boolean(formik.errors.knockOutStageFormat)}
            >
              {knockOutStageFormats.map((format) => (
                <MenuItem key={format.format_id} value={format.format_id}>
                  {format.format_name}
                </MenuItem>
              ))}
            </Select>
            {formik.touched.knockOutStageFormat && formik.errors.knockOutStageFormat && (
              <Typography variant="caption" color="error">{formik.errors.knockOutStageFormat}</Typography>
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
              disabled={formik.values.groupStageFormat === '1'}
            >
              {numberOfGroupsOptions.map((option) => (
                <MenuItem key={`number-of-groups-${option}`} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
            {formik.touched.numberOfGroups && formik.errors.numberOfGroups && (
              <Typography variant="caption" color="error">{formik.errors.numberOfGroups}</Typography>
            )}
          </FormControl>


          <FormControl fullWidth variant="outlined">
            <InputLabel id="advancing-players-label">Advancing Players</InputLabel>
            <Select
              labelId="advancing-players-label"
              name="advancingPlayers"
              value={formik.values.advancingPlayers}
              onChange={formik.handleChange}
              label="Advancing Players"
              error={formik.touched.advancingPlayers && Boolean(formik.errors.advancingPlayers)}
              disabled={formik.values.knockOutStageFormat === '1'} // Assuming '1' is the value for "Keine Knock-Out Stage"
            >
              <MenuItem value={1}>1</MenuItem>
              <MenuItem value={2}>2</MenuItem>
            </Select>
            {formik.touched.advancingPlayers && formik.errors.advancingPlayers && (
              <Typography variant="caption" color="error">{formik.errors.advancingPlayers}</Typography>
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

      
        <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Button variant="contained" color="secondary" type="submit">
            Turnier starten
          </Button>
          {error && (
            <Typography variant="body2" color="error" sx={{ mt: 1 }}>
              {error}
            </Typography>
          )}
        </Box>
      </form>
    </Box>
  );
};

export default Tournament;
