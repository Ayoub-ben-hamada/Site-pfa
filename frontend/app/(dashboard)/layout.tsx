"use client"

import { useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth, AuthProvider } from "@/lib/auth"
import { Loader2 } from "lucide-react"

function DashboardLayoutContent({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login")
    }
  }, [user, isLoading, router])

  useEffect(() => {
    if (!isLoading && user) {
      // Check if user is accessing correct dashboard
      const path = pathname.split("/")[1]
      if (path === "client" && user.role !== "client") {
        router.push(`/${user.role}`)
      } else if (path === "admin" && user.role !== "admin") {
        router.push(`/${user.role}`)
      } else if (path === "directeur" && user.role !== "directeur") {
        router.push(`/${user.role}`)
      }
    }
  }, [user, isLoading, pathname, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!user) {
    return null
  }

  return <>{children}</>
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <DashboardLayoutContent>{children}</DashboardLayoutContent>
    </AuthProvider>
  )
}
