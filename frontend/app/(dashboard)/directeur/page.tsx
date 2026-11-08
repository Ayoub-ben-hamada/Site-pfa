"use client"

import useSWR from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { KpiCard } from "@/components/kpi-card"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { dashboardApi } from "@/lib/api"
import {
  BarChart3,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ThumbsUp,
  MessageSquareWarning,
  Loader2,
  Info,
  AlertCircle,
} from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"

const fetcher = () => dashboardApi.getKpis()

export default function DirectorDashboardPage() {
  const { data: kpis, isLoading } = useSWR("dashboard-kpis", fetcher)

  const getAlertIcon = (type: string) => {
    switch (type) {
      case "danger":
        return <AlertCircle className="h-4 w-4" />
      case "warning":
        return <AlertTriangle className="h-4 w-4" />
      default:
        return <Info className="h-4 w-4" />
    }
  }

  const getAlertVariant = (type: string) => {
    switch (type) {
      case "danger":
        return "destructive"
      default:
        return "default"
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-screen bg-background">
        <AppSidebar />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </main>
      </div>
    )
  }

  const kpiCards = [
    {
      title: "Total Installations",
      value: kpis?.nb_installations || 0,
      icon: BarChart3,
      color: "primary" as const,
      description: "Installations enregistrées",
    },
    {
      title: "Taux de Réussite",
      value: kpis?.taux_reussite || 0,
      suffix: "%",
      icon: CheckCircle2,
      color: kpis?.taux_reussite >= 70 ? "success" as const : "warning" as const,
      trend: kpis?.taux_reussite >= 70 ? "up" as const : "down" as const,
      trendValue: kpis?.taux_reussite >= 70 ? "Bon niveau" : "À améliorer",
    },
    {
      title: "Taux de Satisfaction",
      value: kpis?.taux_satisfaction || 0,
      suffix: "%",
      icon: ThumbsUp,
      color: kpis?.taux_satisfaction >= 60 ? "success" as const : "warning" as const,
    },
    {
      title: "Taux de Réclamation",
      value: kpis?.taux_reclamation || 0,
      suffix: "%",
      icon: MessageSquareWarning,
      color: kpis?.taux_reclamation <= 40 ? "success" as const : "destructive" as const,
    },
    {
      title: "Durée Moyenne",
      value: kpis?.duree_moyenne || 0,
      suffix: "min",
      icon: Clock,
      color: "accent" as const,
    },
    {
      title: "Clients à Risque",
      value: kpis?.taux_clients_risque || 0,
      suffix: "%",
      icon: AlertTriangle,
      color: kpis?.taux_clients_risque <= 30 ? "success" as const : "destructive" as const,
    },
  ]

  // Sample data for charts (based on KPIs)
  const successRateData = [
    { name: "Réussite", value: kpis?.taux_reussite || 0, fill: "hsl(var(--chart-3))" },
    { name: "Échec", value: 100 - (kpis?.taux_reussite || 0), fill: "hsl(var(--chart-5))" },
  ]

  const serviceHealthData = [
    {
      name: "Satisfaction",
      positif: kpis?.taux_satisfaction || 0,
      negatif: 100 - (kpis?.taux_satisfaction || 0),
    },
    {
      name: "Réclamation",
      positif: 100 - (kpis?.taux_reclamation || 0),
      negatif: kpis?.taux_reclamation || 0,
    },
    {
      name: "Risque",
      positif: 100 - (kpis?.taux_clients_risque || 0),
      negatif: kpis?.taux_clients_risque || 0,
    },
  ]

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Vue Globale - KPI</h1>
            <p className="text-muted-foreground">
              Tableau de bord décisionnel pour la supervision des installations CNI
            </p>
          </div>

          {/* Alerts */}
          {kpis?.alerts && kpis.alerts.length > 0 && (
            <div className="grid gap-4 mb-8">
              {kpis.alerts.map((alert: any, index: number) => (
                <Alert key={index} variant={getAlertVariant(alert.type) as any}>
                  {getAlertIcon(alert.type)}
                  <AlertTitle className="ml-2">Alerte</AlertTitle>
                  <AlertDescription className="ml-2">{alert.message}</AlertDescription>
                </Alert>
              ))}
            </div>
          )}

          {/* KPI Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {kpiCards.map((kpi) => (
              <KpiCard key={kpi.title} {...kpi} />
            ))}
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Taux de Réussite des Installations</CardTitle>
                <CardDescription>Répartition réussite / échec</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={successRateData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={2}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                      >
                        {successRateData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-chart-3" />
                    <span className="text-sm text-muted-foreground">Réussite</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-chart-5" />
                    <span className="text-sm text-muted-foreground">Échec</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Santé Client et Qualité de Service</CardTitle>
                <CardDescription>Lecture consolidée des signaux positifs vs négatifs</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={serviceHealthData} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="name" tickLine={false} axisLine={false} />
                      <YAxis domain={[0, 100]} tickLine={false} axisLine={false} />
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                      <Bar dataKey="positif" stackId="a" fill="#00A6A6" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="negatif" stackId="a" fill="#F25F5C" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#00A6A6" }} />
                    <span className="text-sm text-muted-foreground">Positif / maîtrisé</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#F25F5C" }} />
                    <span className="text-sm text-muted-foreground">Négatif / à corriger</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

        </div>
      </main>
    </div>
  )
}
