'use client';

import { useState, useEffect } from 'react';
import { getCurrentUser, User as DjangoUser } from '@/lib/auth';

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  username?: string;
  first_name?: string;
  last_name?: string;
}

// Fetch actual user from Django backend
export function useUser() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchUser() {
      try {
        const djangoUser = await getCurrentUser();
        if (djangoUser) {
          // Transform Django user to our User interface
          const fullName = [djangoUser.first_name, djangoUser.last_name]
            .filter(Boolean)
            .join(' ');
          
          setUser({
            id: djangoUser.id.toString(),
            email: djangoUser.email,
            name: fullName || djangoUser.username,
            username: djangoUser.username,
            first_name: djangoUser.first_name,
            last_name: djangoUser.last_name,
          });
        }
      } catch (error) {
        console.error('Error fetching user:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchUser();
  }, []);

  return user;
}
