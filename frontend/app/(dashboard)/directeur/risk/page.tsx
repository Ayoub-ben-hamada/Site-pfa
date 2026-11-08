"use client"

import useSWR from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { dashboardApi } from "@/lib/api"
import { PlotlyFigure } from "@/components/plotly-figure"
import {
  Loader2,
  AlertTriangle,
  Lightbulb,
  CheckCircle2,
  Users,
  Brain,
  TargetIcon,
} from "lucide-react"
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const fetchRisk = () => dashboardApi.getRiskAnalysis()
const fetchDecision = () => dashboardApi.getDecisionSupport(100)

export default function RiskAnalysisPage() {
  const { data: riskData, isLoading: isRiskLoading } = useSWR("dashboard-risk", fetchRisk)
  const { data: decisionData, isLoading: isDecisionLoading } = useSWR("dashboard-decision-support", fetchDecision)

  if (isRiskLoading || isDecisionLoading) {
    return (
      <div className="flex h-screen bg-background">
        <AppSidebar />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </main>
      </div>
    )
  }

  const riskPieData = [
    { name: "À risque", value: riskData?.nb_clients_risque || 0, fill: "hsl(var(--destructive))" },
    { name: "Sains", value: (riskData?.total_clients || 0) - (riskData?.nb_clients_risque || 0), fill: "hsl(var(--chart-3))" },
  ]

  const getRiskBadge = (risque: number) => {
    if (risque >= 0.7) {
      return <Badge className="bg-destructive text-destructive-foreground">Critique ({(risque * 100).toFixed(0)}%)</Badge>
    }
    if (risque >= 0.5) {
      return <Badge className="bg-warning text-warning-foreground">Haute ({(risque * 100).toFixed(0)}%)</Badge>
    }
    if (risque >= 0.3) {
      return <Badge className="bg-chart-4 text-chart-4-foreground">Moyenne ({(risque * 100).toFixed(0)}%)</Badge>
    }
    return <Badge variant="outline">Faible ({(risque * 100).toFixed(0)}%)</Badge>
  }

  const getPriorityBadge = (priority: number) => {
    if (priority === 1) return <Badge className="bg-destructive text-destructive-foreground">Critique</Badge>
    if (priority === 2) return <Badge className="bg-warning text-warning-foreground">Haute</Badge>
    if (priority === 3) return <Badge className="bg-chart-4 text-chart-4-foreground">Moyenne</Badge>
    return <Badge variant="secondary">Normale</Badge>
  }

  const getEffortBadge = (effort: string) => {
    switch (effort) {
      case "Faible":
        return <Badge variant="outline" className="bg-success/10 text-success border-success/20">Faible</Badge>
      case "Moyen":
        return <Badge variant="outline" className="bg-warning/10 text-warning border-warning/20">Moyen</Badge>
      case "Élevé":
        return <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/20">Élevé</Badge>
      default:
        return <Badge variant="outline">{effort}</Badge>
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Aide à la Décision</h1>
            <p className="text-muted-foreground">
              Vue globale du risque, analyse SHAP détaillée et recommandations priorisées
            </p>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-destructive/10 rounded-xl flex items-center justify-center">
                    <AlertTriangle className="w-7 h-7 text-destructive" />
                  </div>
                  <div>
                    <p className="text-3xl font-bold">{riskData?.taux_risque}%</p>
                    <p className="text-sm text-muted-foreground">Taux de clients à risque</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-chart-5/10 rounded-xl flex items-center justify-center">
                    <Users className="w-7 h-7 text-chart-5" />
                  </div>
                  <div>
                    <p className="text-3xl font-bold">{riskData?.nb_clients_risque}</p>
                    <p className="text-sm text-muted-foreground">Clients identifiés à risque</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-success/10 rounded-xl flex items-center justify-center">
                    <CheckCircle2 className="w-7 h-7 text-success" />
                  </div>
                  <div>
                    <p className="text-3xl font-bold">{riskData?.total_clients}</p>
                    <p className="text-sm text-muted-foreground">Total clients analysés</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Répartition des Clients
              </CardTitle>
              <CardDescription>
                Clients à risque vs clients sains
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={riskPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {riskPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-center gap-6 mt-2">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-destructive" />
                  <span className="text-sm text-muted-foreground">À risque</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-chart-3" />
                  <span className="text-sm text-muted-foreground">Sains</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TargetIcon className="w-5 h-5" />
                Analyse SHAP et Recommandations
              </CardTitle>
              <CardDescription>
                Analyse détaillée des clients à risque avec causes (SHAP) et actions recommandées
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Client ID</TableHead>
                      <TableHead>Risque</TableHead>
                      <TableHead>Causes Principales (SHAP)</TableHead>
                      <TableHead>Nombre d&apos;Actions</TableHead>
                      <TableHead>Détails</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {decisionData?.clients?.map((client: any, index: number) => (
                      <TableRow key={index} className={client.risque >= 0.5 ? "bg-destructive/5" : ""}>
                        <TableCell className="font-semibold">{client.client_id}</TableCell>
                        <TableCell>{getRiskBadge(client.risque)}</TableCell>
                        <TableCell className="max-w-xs">
                          <div className="text-sm space-y-1">
                            {client.top_causes?.slice(0, 2).map((cause: string, i: number) => (
                              <div key={i} className="flex items-start gap-2">
                                <Brain className="w-3 h-3 mt-1 text-primary" />
                                <span className="text-muted-foreground truncate">{cause}</span>
                              </div>
                            ))}
                            {client.top_causes?.length > 2 && (
                              <div className="text-xs text-muted-foreground">+{client.top_causes.length - 2} autres</div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{client.top_actions?.length || 0} actions</Badge>
                        </TableCell>
                        <TableCell>
                          <Dialog>
                            <DialogTrigger asChild>
                              <button className="text-primary hover:underline text-sm font-medium">
                                Voir plus
                              </button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl">
                              <DialogHeader>
                                <DialogTitle>Client ID {client.client_id}</DialogTitle>
                                <DialogDescription>Analyse détaillée du risque client</DialogDescription>
                              </DialogHeader>

                              <div className="space-y-6 mt-4">
                                <div>
                                  <h3 className="font-semibold text-lg mb-3">Niveau de Risque</h3>
                                  <div className="flex items-center gap-4">
                                    {getRiskBadge(client.risque)}
                                    <div className="flex-1">
                                      <div className="w-full bg-muted rounded-full h-2">
                                        <div
                                          className={`h-2 rounded-full transition-all ${
                                            client.risque >= 0.7 ? "bg-destructive" :
                                            client.risque >= 0.5 ? "bg-warning" :
                                            client.risque >= 0.3 ? "bg-chart-4" :
                                            "bg-success"
                                          }`}
                                          style={{ width: `${client.risque * 100}%` }}
                                        />
                                      </div>
                                    </div>
                                  </div>
                                </div>

                                {client.top_causes && client.top_causes.length > 0 && (
                                  <div>
                                    <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                                      <Brain className="w-5 h-5 text-primary" />
                                      Causes Principales (SHAP)
                                    </h3>
                                    <div className="space-y-2">
                                      {client.top_causes.map((cause: string, i: number) => (
                                        <div key={i} className="flex items-start gap-3 p-2 bg-muted/50 rounded-lg">
                                          <div className="w-6 h-6 bg-primary/10 rounded flex items-center justify-center text-xs font-semibold">
                                            {i + 1}
                                          </div>
                                          <p className="text-sm mt-0.5">{cause}</p>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {client.top_actions && client.top_actions.length > 0 && (
                                  <div>
                                    <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                                      <Lightbulb className="w-5 h-5 text-warning" />
                                      Actions Recommandées
                                    </h3>
                                    <div className="space-y-2">
                                      {client.top_actions.map((action: any, i: number) => (
                                        <div key={i} className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg border-l-2 border-warning">
                                          <div className="w-6 h-6 bg-warning/10 rounded-full flex items-center justify-center text-xs font-semibold">
                                            {i + 1}
                                          </div>
                                          <div className="flex-1 mt-0.5">
                                            <p className="font-medium text-sm">{action.action || action}</p>
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </DialogContent>
                          </Dialog>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
