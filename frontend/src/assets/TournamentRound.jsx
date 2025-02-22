import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  FormControl,
  Select,
  MenuItem,
} from '@mui/material';

const TournamentRound = () => {
  const { tournamentId } = useParams(); // Get tournamentId from route params
  const [matches, setMatches] = useState([]);
  const [winners, setWinners] = useState({});
  const [error, setError] = useState('');
  const [round, setRound] = useState(1); // Add round state
  const navigate = useNavigate();

  const fetchMatches = async (roundNumber) => {
    try {
      const response = await fetch(`/api/tournaments/${tournamentId}/matches?round_number=${roundNumber}`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const matchesData = await response.json();
      setMatches(matchesData);
    } catch (error) {
      console.error('Error fetching matches:', error);
    }
  };

  useEffect(() => {
    fetchMatches(round);
  }, [tournamentId, round]);

  const handleWinnerChange = async (matchId, winnerId) => {
    setWinners((prevWinners) => ({
      ...prevWinners,
      [matchId]: winnerId,
    }));

    try {
      const response = await fetch(`/api/matches/${matchId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ winner_id: winnerId }),
      });

      if (!response.ok) {
        throw new Error('Failed to update match result');
      }
      console.log(`Match ${matchId} winner updated to player ${winnerId}`);
    } catch (error) {
      console.error('Error updating match result:', error);
    }

};

  const handleNextRound = async () => {
    const allWinnersSelected = matches.every(match => winners[match.match_id]);

    if (!allWinnersSelected) {
      setError('Es sind noch nicht alle Gewinner ausgewählt.');
      return;
    }
    if (matches.length === 1) {
      navigate(`/tournaments/${tournamentId}/winner`);
    } else {
    try {
      const response = await fetch(`/api/next-round/${tournamentId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to create next round matches');
      }

      const result = await response.json();
      console.log('Next round matches created:', result.matches);

      // Check if the tournament is over
      
        // Update the round state to trigger refresh
        fetchMatches(round + 1);
        setRound(prevRound => prevRound + 1)
        
      
        
      
    } catch (error) {
      console.error('Error creating next round matches:', error);
    }
  }
  };


  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Spiele der aktuellen Runde
      </Typography>

      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Gruppe</TableCell>
            <TableCell>Spieler 1</TableCell>
            <TableCell>Spieler 2</TableCell>
            <TableCell>Gewinner</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {matches.map((match) => (
            <TableRow
              key={match.match_id}
              sx={{ '&:last-child td, &:last-child th': { border: 0 }, height: '36px' }} // Reduce row height
            >
              <TableCell sx={{ padding: '6px' }}>{match.group_number}</TableCell> {/* Reduce cell padding */}
              <TableCell sx={{ padding: '6px' }}>{match.player1.name}</TableCell> {/* Reduce cell padding */}
              <TableCell sx={{ padding: '6px' }}>{match.player2.name}</TableCell> {/* Reduce cell padding */}
              <TableCell sx={{ padding: '6px' }}> {/* Reduce cell padding */}
                <FormControl fullWidth variant="outlined" sx={{ minHeight: '36px' }}>
                  <Select
                    value={winners[match.match_id] || ''}
                    onChange={(e) => handleWinnerChange(match.match_id, e.target.value)}
                    displayEmpty
                    sx={{ height: '36px' }} // Reduce select height
                  >
                    <MenuItem value="" disabled>Gewinner auswählen</MenuItem>
                    <MenuItem value={match.player1.player_id}>{match.player1.name}</MenuItem>
                    <MenuItem value={match.player2.player_id}>{match.player2.name}</MenuItem>
                  </Select>
                </FormControl>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Box sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
        <Button variant="contained" color="secondary" onClick={handleNextRound}>
          {matches.length === 1 ? 'Turnier beenden' : 'Nächste Runde'}
        </Button>
        {error && (
          <Typography variant="body2" color="error" sx={{ ml: 2 }}>
            {error}
          </Typography>
        )}
      </Box>
    </Box>
  );
};

export default TournamentRound;
