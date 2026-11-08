"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  BarChart3,
  Package,
  Bell,
  History,
  Users,
  Settings,
  LogOut,
  LayoutDashboard,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  Target,
  Boxes,
  Brain,
} from "lucide-react"

interface NavItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

const clientNav: NavItem[] = [
  { title: "Mes Applications", href: "/client", icon: Package },
  { title: "Notifications", href: "/client/notifications", icon: Bell },
  { title: "Historique", href: "/client/history", icon: History },
]

const adminNav: NavItem[] = [
  { title: "Tableau de bord", href: "/admin", icon: LayoutDashboard },
  { title: "Utilisateurs", href: "/admin/users", icon: Users },
  { title: "Produits", href: "/admin/products", icon: Boxes },
  { title: "Permissions", href: "/admin/permissions", icon: ShieldCheck },
]

const directeurNav: NavItem[] = [
  { title: "Vue Globale", href: "/directeur", icon: LayoutDashboard },
  { title: "Analyse par Variable", href: "/directeur/analysis", icon: Target },
  { title: "Prévisions", href: "/directeur/predictions", icon: TrendingUp },
  { title: "Prédictions ML", href: "/directeur/predictions-ml", icon: Brain },
  { title: "Aide à la Décision", href: "/directeur/risk", icon: Brain },
]

export function AppSidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuth()

  const getNavItems = (): NavItem[] => {
    switch (user?.role) {
      case "client":
        return clientNav
      case "admin":
        return adminNav
      case "directeur":
        return directeurNav
      default:
        return []
    }
  }

  const getRoleLabel = () => {
    switch (user?.role) {
      case "client":
        return "Portail Client"
      case "admin":
        return "Administration"
      case "directeur":
        return "Direction"
      default:
        return ""
    }
  }

  const navItems = getNavItems()

  return (
    <div className="flex h-screen w-64 flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border">
      {/* Header */}
      <div className="flex h-16 items-center gap-3 px-4 border-b border-sidebar-border">
        <div className="w-9 h-9 bg-sidebar-primary rounded-lg flex items-center justify-center">
          <BarChart3 className="w-5 h-5 text-sidebar-primary-foreground" />
        </div>
        <div>
          <span className="font-semibold text-sm">SADP</span>
          <p className="text-xs text-sidebar-foreground/60">{getRoleLabel()}</p>
        </div>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== `/${user?.role}` && pathname.startsWith(item.href + "/"))
            
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                )}
              >
                <item.icon className="w-4 h-4" />
                {item.title}
              </Link>
            )
          })}
        </nav>
      </ScrollArea>

      {/* Footer */}
      <div className="p-3 border-t border-sidebar-border">
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="w-8 h-8 bg-sidebar-accent rounded-full flex items-center justify-center text-xs font-semibold">
            {(user?.name?.charAt(0) || user?.email?.charAt(0) || "C").toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-sidebar-foreground/60 truncate">{user?.email}</p>
          </div>
        </div>
        <Button
          variant="ghost"
          className="w-full justify-start text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent/50"
          onClick={logout}
        >
          <LogOut className="w-4 h-4 mr-2" />
          Déconnexion
        </Button>
      </div>
    </div>
  )
}
