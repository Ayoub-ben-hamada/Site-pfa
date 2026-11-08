"use client"

import { useState } from "react"
import useSWR from "swr"
import { Loader2 } from "lucide-react"
import { AppSidebar } from "@/components/app-sidebar"
import { PlotlyFigure } from "@/components/plotly-figure"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { dashboardApi } from "@/lib/api"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const variables = [
  { value: "installation_reussie", label: "Installation Réussie" },
  { value: "client_satisfait", label: "Client Satisfait" },
  { value: "client_a_reclame", label: "Client a Réclamé" },
  { value: "Duree_installation_minutes", label: "Durée Installation (min)" },
  { value: "nombre_essais_installation", label: "Nombre d'Essais" },
]

function riskBadgeClass(level?: string) {
  switch (level) {
    case "Critique":
      return "bg-red-600 text-white hover:bg-red-600"
    case "Élevé":
      return "bg-orange-500 text-white hover:bg-orange-500"
    case "Modéré":
      return "bg-amber-500 text-white hover:bg-amber-500"
    case "Faible":
      return "bg-emerald-600 text-white hover:bg-emerald-600"
    default:
      return ""
  }
}

function formatMetric(value: unknown, digits = 3) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "-"
  }
  return value.toFixed(digits)
}

export default function AnalysisPage() {
  const [selectedVariable, setSelectedVariable] = useState("installation_reussie")
  const { data: targetData, isLoading: isTargetLoading } = useSWR(
    ["dashboard-target", selectedVariable],
    () => dashboardApi.getTargetAnalysis(selectedVariable),
    { revalidateOnFocus: false }
  )
  const { data: predictionsData, isLoading: isPredictionsLoading } = useSWR(
    "dashboard-predictions",
    () => dashboardApi.getPredictions(),
    { revalidateOnFocus: false }
  )
  const { data: decisionData, isLoading: isDecisionLoading } = useSWR(
    "dashboard-decision-support",
    () => dashboardApi.getDecisionSupport(20),
    { revalidateOnFocus: false }
  )
  const selectedLabel = variables.find((v) => v.value === selectedVariable)?.label ?? selectedVariable

  const modelTrends = predictionsData?.trends ?? []
  const arimaForecast = predictionsData?.arima_forecast ?? []
  const decisionRows = decisionData?.clients ?? []

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      
      <main className="flex-1 overflow-auto">
        <div className="p-8 space-y-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Analyse par Variable Cible</h1>
              <p className="text-muted-foreground">
                Analysez les facteurs influençant chaque métrique clé, les résultats modèles et les prévisions.
              </p>
            </div>
            <Select value={selectedVariable} onValueChange={setSelectedVariable}>
              <SelectTrigger className="w-70">
                <SelectValue placeholder="Sélectionner une variable" />
              </SelectTrigger>
              <SelectContent>
                {variables.map((v) => (
                  <SelectItem key={v.value} value={v.value}>
                    {v.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {isTargetLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : targetData ? (
            <div className="space-y-8">
              {targetData?.plotly_figures?.temporal && (
                <Card>
                  <CardHeader>
                    <CardTitle>Analyse temporelle</CardTitle>
                    <CardDescription>
                      Évolution de {selectedLabel} selon les mois.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <PlotlyFigure figure={targetData.plotly_figures.temporal} height={360} />
                  </CardContent>
                </Card>
              )}

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {targetData?.plotly_figures?.by_zone_urbanisation && (
                  <Card>
                    <CardHeader>
                      <CardTitle>{selectedLabel} par zone d'urbanisation</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <PlotlyFigure figure={targetData.plotly_figures.by_zone_urbanisation} height={320} />
                    </CardContent>
                  </Card>
                )}

                {targetData?.plotly_figures?.by_product && (
                  <Card>
                    <CardHeader>
                      <CardTitle>{selectedLabel} par produit</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <PlotlyFigure figure={targetData.plotly_figures.by_product} height={320} />
                    </CardContent>
                  </Card>
                )}

                {targetData?.plotly_figures?.os_performance && (
                  <Card>
                    <CardHeader>
                      <CardTitle>{selectedLabel} par système d'exploitation</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <PlotlyFigure figure={targetData.plotly_figures.os_performance} height={320} />
                    </CardContent>
                  </Card>
                )}

                {targetData?.plotly_figures?.kpi_version && (
                  <Card>
                    <CardHeader>
                      <CardTitle>{selectedLabel} par version de produit</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <PlotlyFigure figure={targetData.plotly_figures.kpi_version} height={320} />
                    </CardContent>
                  </Card>
                )}

                {targetData?.plotly_figures?.client_pie && (
                  <Card>
                    <CardHeader>
                      <CardTitle>{selectedLabel} par type client</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <PlotlyFigure figure={targetData.plotly_figures.client_pie} height={320} />
                    </CardContent>
                  </Card>
                )}

                {targetData?.plotly_figures?.kpi_cat_debit && (
                  <Card>
                    <CardHeader>
                      <CardTitle>{selectedLabel} par catégorie de débit</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <PlotlyFigure figure={targetData.plotly_figures.kpi_cat_debit} height={320} />
                    </CardContent>
                  </Card>
                )}

                {targetData?.plotly_figures?.problems_histogram && (
                  <Card className="xl:col-span-2">
                    <CardHeader>
                      <CardTitle>Histogramme des problèmes détectés</CardTitle>
                      <CardDescription>
                        Répartition des problèmes enregistrés pour {selectedLabel}.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <PlotlyFigure figure={targetData.plotly_figures.problems_histogram} height={320} />
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">Aucune donnée disponible</p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}
