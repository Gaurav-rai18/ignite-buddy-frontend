import {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from 'react';

import { usersService } from '../services/usersService';
import { formatErrorMessage, isRequestCancellation } from '../utils/error';

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

  const fetchUsers = useCallback(async (signal) => {
    setLoading(true);
    setError('');

    try {
      const validSignal =
        signal && typeof signal.addEventListener === 'function' ? signal : undefined;
      const data = await usersService.getUsers(validSignal ? { signal: validSignal } : {});

      if (isMountedRef.current) {
        setUsers(data);
      }
    } catch (err) {
      if (isMountedRef.current && !isRequestCancellation(err)) {
        setError(formatErrorMessage(err));
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchUsers(controller.signal);
    return () => controller.abort();
  }, [fetchUsers]);

  const addUser = useCallback(
    async (userData) => {
      const created =
        await usersService.createUser(userData);

      if (isMountedRef.current) {
        setUsers((prev) => [
          created,
          ...prev,
        ]);
      }

      return created;
    },
    []
  );

  const editUser = useCallback(
    async (userId, userData) => {
      const updated =
        await usersService.updateUser(
          userId,
          userData
        );

      if (isMountedRef.current) {
        setUsers((prev) =>
          prev.map((u) =>
            (u.id === userId || (updated && u.id === updated.id))
              ? { ...u, ...updated, id: u.id || updated?.id || userId }
              : u
          )
        );
      }

      return updated;
    },
    []
  );

  const deleteUser = useCallback(
    async (userId) => {
      await usersService.deleteUser(userId);

      if (isMountedRef.current) {
        setUsers((prev) =>
          prev.filter(
            (u) => u.id !== userId
          )
        );
      }
    },
    []
  );

  const filteredUsers = useMemo(() => {
    if (!searchQuery.trim()) {
      return users;
    }

    const q = searchQuery
      .toLowerCase()
      .trim();

    return users.filter(
      (u) =>
        u.username?.toLowerCase().includes(q) ||
        u.email?.toLowerCase().includes(q) ||
        u.role?.toLowerCase().includes(q) ||
        u.employee_id?.toLowerCase().includes(q) ||
        u.full_batch_name?.toLowerCase().includes(q) ||
        u.cohort_code?.toLowerCase().includes(q)
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
    refetch: () => fetchUsers(),
  };
}
