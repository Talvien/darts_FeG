import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';

const TournamentWinner = () => {
  const { tournamentId } = useParams();
  const [players, setPlayers] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPlayerRankings = async () => {
      try {
        const response = await fetch(`/api/tournaments/${tournamentId}/rankings`);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const playersData = await response.json();
        setPlayers(playersData);
      } catch (error) {
        console.error('Error fetching player rankings:', error);
        setError('Error fetching player rankings.');
      }
    };

    fetchPlayerRankings();
  }, [tournamentId]);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Spieler-Rankings
      </Typography>

      {error && (
        <Typography variant="body2" color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Rang</TableCell>
            <TableCell>Spieler</TableCell>
            <TableCell>Gewonnene Spiele</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {players.map((player, index) => (
            <TableRow key={player.player_id}>
              <TableCell>{index + 1}</TableCell>
              <TableCell>{player.name}</TableCell>
              <TableCell>{player.matches_won}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  );
};

export default TournamentWinner;
