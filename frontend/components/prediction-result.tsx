"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { PredictionResponse } from "@/lib/api"

type PredictionResultProps = {
  result: PredictionResponse | null
}

export function PredictionResult({ result }: PredictionResultProps) {
  if (!result) {
    return (
      <Card>
        <CardContent className="pt-6 text-sm text-muted-foreground">
          Lancez une prédiction pour afficher le résultat ici.
        </CardContent>
      </Card>
    )
  }

  const isClassification = result.model_type === "classification"
  const confidence = typeof result.confidence === "number" ? Math.round(result.confidence * 100) : null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between gap-4">
          <span>{result.display_name}</span>
          <Badge variant={isClassification ? (result.prediction === 1 ? "default" : "secondary") : "outline"}>
            {isClassification ? (result.prediction === 1 ? "OUI" : "NON") : `${result.prediction.toFixed(1)} min`}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm text-muted-foreground">{result.message}</p>
        </div>

        {isClassification && typeof result.probability === "number" && (
          <div className="space-y-2 rounded-lg bg-muted/40 p-4">
            <div className="flex items-center justify-between text-sm">
              <span>Probabilité positive</span>
              <span className="font-medium">{(result.probability * 100).toFixed(1)}%</span>
            </div>
            <div className="h-2 rounded-full bg-muted">
              <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.round(result.probability * 100)}%` }} />
            </div>
            {confidence !== null && <p className="text-xs text-muted-foreground">Confiance estimée: {confidence}%</p>}
          </div>
        )}

        {!isClassification && (
          <div className="rounded-lg bg-muted/40 p-4 text-sm">
            <p className="font-medium">Estimation de durée</p>
            <p className="text-muted-foreground">Le modèle de régression retourne le temps estimé d'installation.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}