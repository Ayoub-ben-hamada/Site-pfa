"use client"

import useSWR from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { adminApi } from "@/lib/api"
import { Users, Package, ShieldCheck, BarChart3 } from "lucide-react"

export default function AdminDashboardPage() {
  const { data: users } = useSWR("admin-users", () => adminApi.getUsers())
  const { data: products } = useSWR("admin-products", () => adminApi.getProducts())

  const stats = [
    {
      title: "Utilisateurs",
      value: users?.length || 0,
      description: "Comptes actifs",
      icon: Users,
      color: "text-chart-1",
      bgColor: "bg-chart-1/10",
    },
    {
      title: "Produits",
      value: products?.length || 0,
      description: "Dans le catalogue",
      icon: Package,
      color: "text-chart-2",
      bgColor: "bg-chart-2/10",
    },
    {
      title: "Clients",
      value: users?.filter((u: any) => u.role === "client").length || 0,
      description: "Utilisateurs clients",
      icon: ShieldCheck,
      color: "text-chart-3",
      bgColor: "bg-chart-3/10",
    },
    {
      title: "Admins",
      value: users?.filter((u: any) => u.role === "admin" || u.role === "directeur").length || 0,
      description: "Administrateurs",
      icon: BarChart3,
      color: "text-chart-4",
      bgColor: "bg-chart-4/10",
    },
  ]

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Administration</h1>
            <p className="text-muted-foreground">
              Gérez les utilisateurs, les produits et les permissions du système CNI
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {stats.map((stat) => (
              <Card key={stat.title}>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 ${stat.bgColor} rounded-xl flex items-center justify-center`}>
                      <stat.icon className={`w-6 h-6 ${stat.color}`} />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{stat.value}</p>
                      <p className="text-sm text-muted-foreground">{stat.description}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Derniers Utilisateurs</CardTitle>
                <CardDescription>Utilisateurs récemment ajoutés au système</CardDescription>
              </CardHeader>
              <CardContent>
                {users && users.length > 0 ? (
                  <div className="space-y-3">
                    {users.slice(0, 5).map((user: any) => (
                      <div key={user.id} className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                        <div className="w-9 h-9 bg-primary/10 rounded-full flex items-center justify-center text-sm font-semibold text-primary">
                          {user.name.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm truncate">{user.name}</p>
                          <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                        </div>
                        <span className="text-xs px-2 py-1 bg-secondary rounded-full capitalize">
                          {user.role}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Aucun utilisateur</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Catalogue Produits</CardTitle>
                <CardDescription>Produits CNI disponibles</CardDescription>
              </CardHeader>
              <CardContent>
                {products && products.length > 0 ? (
                  <div className="space-y-3">
                    {products.map((product: any) => (
                      <div key={product.id} className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                        <div className="w-9 h-9 bg-gradient-to-br from-primary to-primary/60 rounded-lg flex items-center justify-center text-sm font-bold text-primary-foreground">
                          {product.name.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm">{product.name}</p>
                          <p className="text-xs text-muted-foreground">{product.category}</p>
                        </div>
                        <span className="text-xs px-2 py-1 bg-secondary rounded-full">
                          v{product.latest_version}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Aucun produit</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
