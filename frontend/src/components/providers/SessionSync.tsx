'use client'

import { useSession } from 'next-auth/react'
import { useEffect } from 'react'

export function SessionSync() {
  const { data: session, status } = useSession()

  useEffect(() => {
    if (status === 'authenticated' && session?.accessToken) {
      // Sync the access token to localStorage for the API client
      localStorage.setItem('access_token', session.accessToken)
      if (session.refreshToken) {
        localStorage.setItem('refresh_token', session.refreshToken)
      }
    } else if (status === 'unauthenticated') {
      // Clear tokens when logged out
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }, [session, status])

  return null
}
