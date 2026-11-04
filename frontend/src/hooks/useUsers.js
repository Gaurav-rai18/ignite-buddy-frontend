/**
 * @file useUsers.js
 * @description Custom hook for user management (CRUD + search).
 *
 * Fetches the full user list on mount, provides addUser/editUser/deleteUser
 * actions that optimistically update local state after API success, and
 * exposes a filteredUsers list via useMemo for client-side search.
 *
 * Data flow:
 *   ManageUsers page → useUsers() → usersService → apiClient → Django /api/users/
 *
 * @exports {Function} useUsers - Hook returning users, search, and CRUD actions.
 */
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { usersService } from '../services/usersService';

export function useUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await usersService.getUsers();
      if (isMountedRef.current) {
        setUsers(data);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err.message || 'Failed to load users');
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const addUser = useCallback(async (userData) => {
    const created = await usersService.createUser(userData);
    if (isMountedRef.current) {
      setUsers((prev) => [created, ...prev]);
    }
    return created;
  }, []);

  const editUser = useCallback(async (userId, userData) => {
    const updated = await usersService.updateUser(userId, userData);
    if (isMountedRef.current) {
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
    }
    return updated;
  }, []);

  const deleteUser = useCallback(async (userId) => {
    await usersService.deleteUser(userId);
    if (isMountedRef.current) {
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    }
  }, []);

  const filteredUsers = useMemo(() => {
    if (!searchQuery.trim()) return users;
    const q = searchQuery.toLowerCase().trim();
    return users.filter(
      (u) =>
        (u.username || '').toLowerCase().includes(q) ||
        (u.email || '').toLowerCase().includes(q) ||
        (u.batch || '').toLowerCase().includes(q) ||
        (u.subbatch || '').toLowerCase().includes(q)
    );
  }, [users, searchQuery]);

  return {
    users,
    filteredUsers,
    loading,
    error,
    searchQuery,
    setSearchQuery,
    addUser,
    editUser,
    deleteUser,
    refetch: fetchUsers,
  };
}
