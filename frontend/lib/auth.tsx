"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { useRouter } from "next/navigation"
import { authApi } from "@/lib/api"

interface User {
  id: number
  email: string
  name: string
  role: "client" | "admin" | "directeur"
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const savedToken = localStorage.getItem("cni_token")
    const savedUser = localStorage.getItem("cni_user")
    
    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const data = await authApi.login(email, password)
    
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem("cni_token", data.access_token)
    localStorage.setItem("cni_user", JSON.stringify(data.user))

    // Redirect based on role
    switch (data.user.role) {
      case "client":
        router.push("/client")
        break
      case "admin":
        router.push("/admin")
        break
      case "directeur":
        router.push("/directeur")
        break
      default:
        router.push("/")
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem("cni_token")
    localStorage.removeItem("cni_user")
    router.push("/login")
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
