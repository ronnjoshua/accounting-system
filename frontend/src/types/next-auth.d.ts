import 'next-auth'

declare module 'next-auth' {
  interface Session {
    accessToken: string
    refreshToken: string
    user: {
      id: string
      name?: string | null
      email?: string | null
      image?: string | null
      roles: string[]
    }
  }

  interface User {
    id: string
    email: string
    name: string
    accessToken: string
    refreshToken: string
    roles: string[]
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    accessToken?: string
    refreshToken?: string
    roles?: string[]
    id?: string
  }
}
