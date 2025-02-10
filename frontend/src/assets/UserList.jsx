// client/src/components/UserList.js
import React, { useEffect, useState } from 'react';
import UserCard from './UserCard';


function UserList() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchUsers() {
      try {
        const response = await fetch('/api/users');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const usersData = await response.json();
        setUsers(usersData);
      } catch (error) {
        setError(error.message);
      }
    }
    
    fetchUsers();
  }, []);

  return (
    <div>
      <h2>User List</h2>
      {error && <p>Error: {error}</p>}
      <ul>
        {users.map(user => (
          <li key={user.id}>
            <UserCard user={user} />
          </li>
        ))}
      </ul>
    </div>
  );
}

export default UserList;