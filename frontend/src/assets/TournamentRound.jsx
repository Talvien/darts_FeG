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
  MenuItem
} from '@mui/material';

const TournamentRound = () => {
  const { tournamentId } = useParams(); // Get tournamentId from route params
  const [matches, setMatches] = useState([]);
  const [winners, setWinners] = useState({});
  const [secondPlaces, setSecondPlaces] = useState({});
  const [error, setError] = useState('');
  const [round, setRound] = useState(1); // Add round state
  const [hasGroupPhase, setHasGroupPhase] = useState(false);
  const [isTiebreaker, setIsTiebreaker] = useState(false);
  const [hasPlayer3, setHasPlayer3] = useState(false);
  const navigate = useNavigate();

  const fetchMatches = async (roundNumber) => {
    try {
      const response = await fetch(`/api/tournaments/${tournamentId}/matches?round_number=${roundNumber}`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const matchesData = await response.json();
      setMatches(matchesData);
      setHasGroupPhase(matchesData.some(match => match.group_number !== null));
      setHasPlayer3(matchesData.some(match => match.player3 !== null));
    } catch (error) {
      console.error('Error fetching matches:', error);
    }
  };

  useEffect(() => {
    fetchMatches(round);
  }, [tournamentId, round]);

  const handleMatchUpdate = async (matchId, winnerId, secondPlaceId) => {
    setWinners((prevWinners) => ({
      ...prevWinners,
      [matchId]: winnerId,
    }));
  
    setSecondPlaces((prevSecondPlaces) => ({
      ...prevSecondPlaces,
      [matchId]: secondPlaceId,
    }));
  
    try {
      const response = await fetch(`/api/matches/${matchId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ winner_id: winnerId, second_place_id: secondPlaceId }),  // Send both IDs
      });
  
      if (!response.ok) {
        throw new Error('Failed to update match result');
      }
      console.log(`Match ${matchId} result updated. Winner: ${winnerId}, Second Place: ${secondPlaceId}`);
    } catch (error) {
      console.error('Error updating match result:', error);
    }
  }

  const handleNextRound = async () => {
    const allWinnersSelected = matches.every(match => winners[match.match_id]);

    if (!allWinnersSelected) {
      setError('Es sind noch nicht alle Gewinner ausgewählt.');
      return;
    }
    if (matches.length === 1 &&  !isTiebreaker) {
      navigate(`/tournaments/${tournamentId}/winner`);
    } else {
      if (round === 1) {
        try {
          const response = await fetch(`/api/tournaments/${tournamentId}/tiebreakers/check`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
          });
    
          if (!response.ok) {
            throw new Error('Failed to check tiebreakers');
          }
    
          const result = await response.json();
          console.log('Tiebreakers found:', result.tiebreakers);
          if (result.tiebreakers.length > 0) {
            await handleTiebreaker(); // Call the handleTiebreaker function;
            return;
          }
        } catch (error) {
          console.error('Error checking for tiebreakers:', error);
          return;
        }
      }
    
      // No tiebreakers, proceed to next round
      try {
        const responseNextRound = await fetch(`/api/next-round/${tournamentId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
    
        if (!responseNextRound.ok) {
          throw new Error('Failed to create next round matches');
        }
    
        const resultNextRound = await responseNextRound.json();
        console.log('Next round matches created:', resultNextRound.matches);
        
        setIsTiebreaker(false);
        fetchMatches(round + 1);
        setRound(prevRound => prevRound + 1);
      } catch (error) {
        console.error('Error creating next round matches:', error);
      }
    };
  };

  const handleTiebreaker = async () => {
    try {
      const response = await fetch(`/api/tournaments/${tournamentId}/tiebreakers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
  
      if (!response.ok) {
        throw new Error('Failed to create tiebreaker matches');
      }
  
      const result = await response.json();
      console.log('Tiebreaker matches created:', result.tiebreakers);
      setMatches(result.tiebreakers); // Set the matches to the tiebreakers
      setIsTiebreaker(true); // Set the tiebreaker state to true
      setHasPlayer3(result.tiebreakers.some(match => match.player3 !== null));  
    } catch (error) {
      console.error('Error creating tiebreaker matches:', error);
    }
  };
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
      {round === 1 && hasGroupPhase ? 'Matches Gruppenphase' : isTiebreaker ? 'Tiebreaker-Matches' : `Matches Runde ${round}`}
      </Typography>

      <Table>
      <TableHead>
        <TableRow>
          <TableCell>Gruppe</TableCell>
          <TableCell>Spieler 1</TableCell>
          <TableCell>Spieler 2</TableCell>
          {hasPlayer3 && <TableCell>Spieler 3</TableCell>}
          <TableCell>Gewinner</TableCell>
          {hasPlayer3 && <TableCell>2. Gewinner</TableCell>}
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
            {hasPlayer3 && <TableCell sx={{ padding: '6px' }}>{match.player3 ? match.player3.name : 'N/A'}</TableCell>}
            <TableCell sx={{ padding: '6px' }}> {/* Reduce cell padding */}
              <FormControl fullWidth variant="outlined" sx={{ minHeight: '36px' }}>
                <Select
                  value={winners[match.match_id] || ''}
                  onChange={(e) => handleMatchUpdate(match.match_id, e.target.value, secondPlaces[match.match_id] || null)}
                  displayEmpty
                  sx={{ height: '36px' }} // Reduce select height
                >
                  <MenuItem value="" disabled>Gewinner auswählen</MenuItem>
                  <MenuItem value={match.player1.player_id}>{match.player1.name}</MenuItem>
                  <MenuItem value={match.player2.player_id}>{match.player2.name}</MenuItem>
                  {hasPlayer3 && match.player3 && (
                    <MenuItem value={match.player3.player_id}>{match.player3.name}</MenuItem>
                  )}
                </Select>
              </FormControl>
            </TableCell>
            {hasPlayer3 && (
              <TableCell sx={{ padding: '6px' }}> {/* Reduce cell padding */}
                <FormControl fullWidth variant="outlined" sx={{ minHeight: '36px' }}>
                  <Select
                    value={secondPlaces[match.match_id] || ''}
                    onChange={(e) => handleMatchUpdate(match.match_id, winners[match.match_id] || null, e.target.value)}
                    displayEmpty
                    sx={{ height: '36px' }} // Reduce select height
                  >
                    <MenuItem value="" disabled>Zweiter Platz auswählen</MenuItem>
                    <MenuItem value={match.player1.player_id}>{match.player1.name}</MenuItem>
                    <MenuItem value={match.player2.player_id}>{match.player2.name}</MenuItem>
                    {hasPlayer3 && match.player3 && (
                      <MenuItem value={match.player3.player_id}>{match.player3.name}</MenuItem>
                    )}
                  </Select>
                </FormControl>
              </TableCell>
            )}
          </TableRow>
        ))}
      </TableBody>
    </Table>

    <Box sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
      <Button variant="contained" color="secondary" onClick={handleNextRound}>
        {matches.length === 1 && !isTiebreaker ? 'Turnier beenden' : 'Nächste Runde'}
      </Button>
      {error && (
        <Typography variant="body2" color="error" sx={{ ml: 2 }}>
          {error}
        </Typography>
      )}
    </Box>
  </Box>
)};

export default TournamentRound;
