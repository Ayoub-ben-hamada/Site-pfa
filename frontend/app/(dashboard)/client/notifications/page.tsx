"use client"

import useSWR from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { clientApi } from "@/lib/api"
import { Bell, ArrowUpCircle, Loader2, CheckCircle2, Info } from "lucide-react"

const fetcher = () => clientApi.getNotifications()

export default function NotificationsPage() {
  const { data: notifications, isLoading } = useSWR("client-notifications", fetcher)

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "update":
        return <ArrowUpCircle className="w-5 h-5 text-warning" />
      case "success":
        return <CheckCircle2 className="w-5 h-5 text-success" />
      default:
        return <Info className="w-5 h-5 text-primary" />
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Notifications</h1>
            <p className="text-muted-foreground">
              Restez informé des mises à jour et actualités de vos applications
            </p>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : notifications && notifications.length > 0 ? (
            <div className="space-y-4">
              {notifications.map((notification: any) => (
                <Card key={notification.id} className={notification.read ? "opacity-60" : ""}>
                  <CardContent className="py-4">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                        {getNotificationIcon(notification.type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">{notification.title}</h3>
                          {!notification.read && (
                            <Badge variant="secondary" className="text-xs">Nouveau</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">{notification.message}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(notification.date).toLocaleDateString("fr-FR", {
                            day: "numeric",
                            month: "long",
                            year: "numeric",
                          })}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center">
                  <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Aucune notification</h3>
                  <p className="text-muted-foreground">
                    Vous n&apos;avez pas de nouvelles notifications pour le moment.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}
