import React from 'react';
import { useNavigate } from 'react-router-dom';

const NextRoundButton = ({ tournamentId, roundNumber }) => {
  const navigate = useNavigate();

  const handleNextRound = async () => {
    try {
      const response = await fetch(`/next-round/${tournamentId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ round_number: roundNumber }),
      });

      if (!response.ok) {
        throw new Error('Failed to create next round matches');
      }

      const result = await response.json();
      console.log('Next round matches created:', result.matches);
      // Navigate or update the UI as needed
    } catch (error) {
      console.error('Error creating next round matches:', error);
    }
  };

  return (
    <button onClick={handleNextRound}>
      Next Round
    </button>
  );
};

export default NextRoundButton;
