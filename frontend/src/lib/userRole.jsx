import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './auth';
import api from './api';

const UserRoleContext = createContext({ role: null, userProfile: null, roleLoading: true });

export const useUserRole = () => useContext(UserRoleContext);

export const UserRoleProvider = ({ children }) => {
  const { session, loading: authLoading } = useAuth();
  const [role, setRole] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [roleLoading, setRoleLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!session) {
      setRole(null);
      setUserProfile(null);
      setRoleLoading(false);
      return;
    }

    let cancelled = false;
    const fetchRole = async () => {
      try {
        const res = await api.get('/api/v1/users/me');
        if (!cancelled) {
          setRole(res.data.role || null);
          setUserProfile(res.data);
          setRoleLoading(false);
        }
      } catch {
        if (!cancelled) {
          setRole(null);
          setUserProfile(null);
          setRoleLoading(false);
        }
      }
    };
    fetchRole();
    return () => { cancelled = true; };
  }, [session, authLoading]);

  return (
    <UserRoleContext.Provider value={{ role, userProfile, roleLoading }}>
      {children}
    </UserRoleContext.Provider>
  );
};
