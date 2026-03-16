import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { supabase } from './supabase';
import { getErrorMessage } from './api';

const AuthContext = createContext({ user: null, session: null, loading: true });

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const sessionRef = useRef(null);

  useEffect(() => {
    const {
      data: { subscription }
    } = supabase.auth.onAuthStateChange((event, newSession) => {
      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
        sessionRef.current = newSession;
        setSession(newSession);
        setUser(newSession?.user ?? null);
      } else if (event === 'INITIAL_SESSION') {
        if (newSession) {
          sessionRef.current = newSession;
          setSession(newSession);
          setUser(newSession?.user ?? null);
        } else if (!sessionRef.current) {
          // Only clear if we don't already have a valid session
          setSession(null);
          setUser(null);
        }
        // If newSession is null but sessionRef.current exists, skip — keep the good session
      } else if (event === 'SIGNED_OUT') {
        sessionRef.current = null;
        setSession(null);
        setUser(null);
      }
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      if (error) throw error;
      return { data, error: null };
    } catch (error) {
      return { data: null, error: getErrorMessage(error) };
    }
  };

  const signUp = async (email, password, metadata = {}) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: metadata
        }
      });
      if (error) throw error;
      return { data, error: null };
    } catch (error) {
      return { data: null, error: getErrorMessage(error) };
    }
  };

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      return { error: null };
    } catch (error) {
      return { error: getErrorMessage(error) };
    }
  };

  const value = {
    user,
    session,
    loading,
    signIn,
    signUp,
    signOut
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};