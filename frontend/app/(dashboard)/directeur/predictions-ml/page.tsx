"use client"

import { useEffect, useMemo, useState } from "react"
import { toast } from "sonner"
import useSWR from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { PredictionForm } from "@/components/prediction-form"
import { PredictionResult } from "@/components/prediction-result"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, ChevronRight, Brain } from "lucide-react"
import { mlPredictionsApi, PredictionModelMeta, PredictionResponse } from "@/lib/api"

const fetchModels = () => mlPredictionsApi.listModels()

export default function MlPredictionsPage() {
  const { data: models, isLoading, error } = useSWR("ml-predictions-models", fetchModels)
  const [selectedModelName, setSelectedModelName] = useState<string | null>(null)
  const [result, setResult] = useState<PredictionResponse | null>(null)
  const [history, setHistory] = useState<Array<PredictionResponse & { timestamp: string }>>([])
  const [isPredicting, setIsPredicting] = useState(false)

  const selectedModel = useMemo<PredictionModelMeta | null>(() => {
    if (!models || models.length === 0) return null
    return models.find((model) => model.model_name === selectedModelName) || models[0]
  }, [models, selectedModelName])

  useEffect(() => {
    if (models && models.length > 0 && !selectedModelName) {
      setSelectedModelName(models[0].model_name)
    }
  }, [models, selectedModelName])

  const handlePredict = async (features: Record<string, any>) => {
    if (!selectedModel) return
    try {
      setIsPredicting(true)
      const response = await mlPredictionsApi.predict(selectedModel.model_name, features)
      setResult(response)
      setHistory((current) => [
        { ...response, timestamp: new Date().toLocaleString("fr-FR") },
        ...current,
      ].slice(0, 5))
      toast.success("Prédiction effectuée avec succès")
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erreur lors de la prédiction"
      toast.error(message)
    } finally {
      setIsPredicting(false)
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

  if (error) {
    return (
      <div className="flex h-screen bg-background">
        <AppSidebar />
        <main className="flex-1 overflow-auto">
          <div className="p-8">
            <Card>
              <CardContent className="pt-6 text-sm text-destructive">
                Impossible de charger les modèles ML.
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />

      <main className="flex-1 overflow-auto">
        <div className="p-8 space-y-8">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border bg-muted/40 px-3 py-1 text-xs font-medium text-muted-foreground mb-4">
              <Brain className="h-4 w-4" />
              Prédictions ML sur 5 modèles
            </div>
            <h1 className="text-3xl font-bold text-foreground mb-2">Prédictions ML</h1>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-[280px_1fr_360px] gap-6 items-start">
            <Card className="xl:sticky xl:top-6">
              <CardHeader>
                <CardTitle className="text-base">Modèles</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {models?.map((model) => {
                  const active = model.model_name === selectedModel?.model_name
                  return (
                    <button
                      key={model.model_name}
                      type="button"
                      onClick={() => setSelectedModelName(model.model_name)}
                      className={`w-full rounded-xl border px-3 py-3 text-left transition-colors ${active ? "border-primary bg-primary/5" : "hover:bg-muted/50"}`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-medium">{model.display_name}</p>
                          <p className="text-xs text-muted-foreground">{model.model_type === "classification" ? "Classification" : "Régression"}</p>
                        </div>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </button>
                  )
                })}
              </CardContent>
            </Card>

            <div className="space-y-6">
              {selectedModel && (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>{selectedModel.display_name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">{selectedModel.description}</p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        <Badge variant="outline">{selectedModel.model_type}</Badge>
                        <Badge variant="secondary">{selectedModel.input_fields.length} inputs dynamiques</Badge>
                      </div>
                    </CardContent>
                  </Card>

                  <PredictionForm model={selectedModel} onPredict={handlePredict} loading={isPredicting} />
                </>
              )}
            </div>

            <div className="space-y-6 xl:sticky xl:top-6">
              <PredictionResult result={result} />

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Historique</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {history.length === 0 && (
                    <p className="text-sm text-muted-foreground">Aucune prédiction réalisée pour le moment.</p>
                  )}
                  {history.map((item) => (
                    <div key={`${item.model_name}-${item.timestamp}`} className="rounded-lg border p-3 text-sm">
                      <div className="flex items-center justify-between gap-3 mb-1">
                        <span className="font-medium">{item.display_name}</span>
                        <Badge variant="outline">{item.model_type}</Badge>
                      </div>
                      <p className="text-muted-foreground">{item.message}</p>
                      <p className="mt-2 text-xs text-muted-foreground">{item.timestamp}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}