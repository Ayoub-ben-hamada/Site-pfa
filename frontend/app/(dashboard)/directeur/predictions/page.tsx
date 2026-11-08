"use client"

import useSWR from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { dashboardApi } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { PlotlyFigure } from "@/components/plotly-figure"
import { Loader2, TrendingUp, TrendingDown, Minus, Calendar, BarChart3 } from "lucide-react"

const fetchPredictions = () => dashboardApi.getPredictions()

const variableLabels: Record<string, string> = {
  installation_reussie: "Taux de Réussite",
  client_satisfait: "Taux de Satisfaction",
  client_a_reclame: "Taux de Réclamation",
  Duree_installation_minutes: "Durée Installation",
}

export default function PredictionsPage() {
  const { token, isLoading: authLoading } = useAuth()
  const { data, isLoading, error } = useSWR(token ? "dashboard-predictions" : null, fetchPredictions)

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "amélioration":
      case "amelioration":
        return <TrendingUp className="w-4 h-4 text-success" />
      case "dégradation":
      case "degradation":
        return <TrendingDown className="w-4 h-4 text-destructive" />
      default:
        return <Minus className="w-4 h-4 text-muted-foreground" />
    }
  }

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case "amélioration":
      case "amelioration":
        return "bg-success/10 text-success border-success/20"
      case "dégradation":
      case "degradation":
        return "bg-destructive/10 text-destructive border-destructive/20"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  const formatValue = (value: number, variable: string) => {
    if (["installation_reussie", "client_satisfait", "client_a_reclame"].includes(variable)) {
      return `${(value * 100).toFixed(1)}%`
    }
    return value.toFixed(1)
  }

  if (authLoading || isLoading) {
    return (
      <div className="flex h-screen bg-background">
        <AppSidebar />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </main>
      </div>
    )
  }

  const rawPredictions = Array.isArray(data?.predictions) ? data.predictions : []

  const pickNumber = (...values: any[]) => {
    for (const value of values) {
      const parsed = Number(value)
      if (Number.isFinite(parsed)) {
        return parsed
      }
    }
    return Number.NaN
  }

  // Parse backend values defensively to avoid empty charts when types are mixed
  const normalizedPredictions = rawPredictions
    .map((p: any) => ({
      date: String(p?.date ?? ""),
      installation_reussie: pickNumber(p?.installation_reussie, p?.installation_reussie_encoded),
      client_satisfait: pickNumber(p?.client_satisfait, p?.client_satisfait_encoded),
      client_a_reclame: pickNumber(p?.client_a_reclame, p?.client_a_reclame_encoded),
      Duree_installation_minutes: Number(p?.Duree_installation_minutes),
    }))
    .filter((p: any) =>
      p.date.length > 0
      && Number.isFinite(p.installation_reussie)
      && Number.isFinite(p.client_satisfait)
      && Number.isFinite(p.client_a_reclame)
      && Number.isFinite(p.Duree_installation_minutes)
    )

  const hasPredictionData = normalizedPredictions.length > 0

  const arimaFigures = [
    {
      title: "SARIMA - Taux de Réussite",
      figure: data?.plotly_figures?.sarima_installation_reussie_encoded_future || data?.plotly_figures?.arima_installation_reussie_encoded_future || data?.plotly_figures?.arima_installation_reussie_future,
    },
    {
      title: "SARIMA - Satisfaction Client",
      figure: data?.plotly_figures?.sarima_client_satisfait_encoded_future || data?.plotly_figures?.arima_client_satisfait_encoded_future || data?.plotly_figures?.arima_client_satisfait_future,
    },
    {
      title: "SARIMA - Taux de Réclamation",
      figure: data?.plotly_figures?.sarima_client_a_reclame_encoded_future || data?.plotly_figures?.arima_client_a_reclame_encoded_future || data?.plotly_figures?.arima_client_a_reclame_future,
    },
    {
      title: "ARIMA - Durée d'Installation",
      figure: data?.plotly_figures?.sarima_Duree_installation_minutes_future || data?.plotly_figures?.arima_Duree_installation_minutes_future || data?.plotly_figures?.arima_duree,
    },
  ]

  const finetunedModels = Array.isArray(data?.finetuned_models) ? data.finetuned_models : []
  const finetunedModelsFigure = data?.plotly_figures?.finetuned_models

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />

      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Prévisions Futures</h1>
            <p className="text-muted-foreground">
              Prédictions sur 4 semaines pour les 4 modèles principaux
            </p>
          </div>

          {!token ? (
            <Card className="mb-6 border-amber-300 bg-amber-50/60">
              <CardContent className="pt-6">
                <p className="text-sm text-amber-900">
                  Veuillez vous connecter pour afficher les prévisions SARIMA.
                </p>
              </CardContent>
            </Card>
          ) : !hasPredictionData && (
            <Card className="mb-6 border-amber-300 bg-amber-50/60">
              <CardContent className="pt-6">
                <p className="text-sm text-amber-900">
                  {error
                    ? "Impossible de charger les prévisions pour le moment."
                    : (data?.error || data?.message || "Aucune prévision disponible pour le moment. Les modèles sont en cours de préparation.")}
                </p>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {data?.trends?.filter((trend: any) => trend.variable !== "nombre_essais_installation")?.map((trend: any) => (
              <Card key={trend.variable}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-muted-foreground">
                      {variableLabels[trend.variable]}
                    </span>
                    {getTrendIcon(trend.trend)}
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-baseline justify-between">
                      <span className="text-xs text-muted-foreground">Actuel</span>
                      <span className="font-semibold">
                        {formatValue(trend.current, trend.variable)}
                      </span>
                    </div>
                    <div className="flex items-baseline justify-between">
                      <span className="text-xs text-muted-foreground">Prévu</span>
                      <span className="font-bold text-primary">
                        {formatValue(trend.predicted, trend.variable)}
                      </span>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <Badge variant="outline" className={getTrendColor(trend.trend)}>
                      {trend.trend.charAt(0).toUpperCase() + trend.trend.slice(1)}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      Conf: {(trend.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-semibold text-foreground">Prévision SARIMA et ARIMA sur 32 semaines</h2>
                <p className="text-sm text-muted-foreground">
                  4 vues distinctes pour comparer chaque variable aux 32 semaines de prévision SARIMA et ARIMA.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {arimaFigures.map((item) => (
                <Card key={item.title}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="w-5 h-5" />
                      {item.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {item.figure ? (
                      <PlotlyFigure figure={item.figure} height={300} />
                    ) : (
                      <p className="text-sm text-muted-foreground">Aucune prévision ARIMA disponible.</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
