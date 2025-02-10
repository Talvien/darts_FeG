// client/src/components/UserCard.js
import React from 'react';

function UserCard({ user }) {
  return (
    <div>
      <h3>{user.name}</h3>
      <p>ID: {user.id}</p>
    </div>
  );
}

export default UserCard;