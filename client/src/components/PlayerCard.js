import React from 'react';

function PlayerCard({ player }) {
  return (
    <div>
      <h3>{player.name}</h3>
      <p>ID: {player.player_id}</p>
    </div>
  );
}

export default PlayerCard;