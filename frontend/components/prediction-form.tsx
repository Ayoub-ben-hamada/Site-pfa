"use client"

import { useEffect, useState, type FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { PredictionField, PredictionModelMeta } from "@/lib/api"

type PredictionFormProps = {
  model: PredictionModelMeta
  onPredict: (features: Record<string, any>) => Promise<void>
  loading?: boolean
}

const normalizeOptions = (options?: Array<string | { label: string; value: string }>) => {
  return (options || []).map((option) =>
    typeof option === "string" ? { label: option, value: option } : option
  )
}

export function PredictionForm({ model, onPredict, loading = false }: PredictionFormProps) {
  const [formData, setFormData] = useState<Record<string, any>>({})

  useEffect(() => {
    // Start with empty inputs when the page (or model) loads.
    setFormData({})
  }, [model])

  const updateField = (fieldName: string, value: any) => {
    setFormData((current) => ({ ...current, [fieldName]: value }))
  }

  const toggleProblem = (value: string) => {
    // kept for compatibility but delegate to generic update
    setFormData((current) => ({ ...current }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    await onPredict(formData)
  }

  const renderField = (field: PredictionField) => {
    const value = formData[field.name]
    const hasOptions = field.options && field.options.length > 0

    // Afficher un dropdown si le champ a des options (peu importe son type)
    if (field.type === "select" || hasOptions) {
      return (
        <div key={field.name} className="space-y-2">
          <Label htmlFor={field.name}>{field.label}</Label>
          <select
            id={field.name}
            value={value ?? ""}
            onChange={(event) => updateField(field.name, event.target.value)}
            className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm shadow-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring"
          >
            <option value="">{field.placeholder || "Choisir une valeur"}</option>
            {normalizeOptions(field.options).map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      )
    }

    if (field.type === "checkbox-group") {
      const selected = Array.isArray(formData[field.name]) ? formData[field.name] : []
      return (
        <div key={field.name} className="space-y-3">
          <Label>{field.label}</Label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {normalizeOptions(field.options).map((option) => (
              <label key={option.value} className="flex items-center gap-2 rounded-lg border p-3 text-sm">
                <input
                  type="checkbox"
                  checked={selected.includes(option.value)}
                  onChange={() => {
                    const exists = selected.includes(option.value)
                    if (exists) {
                      updateField(field.name, selected.filter((v: string) => v !== option.value))
                    } else {
                      updateField(field.name, [...selected, option.value])
                    }
                  }}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </div>
      )
    }

    return (
      <div key={field.name} className="space-y-2">
        <Label htmlFor={field.name}>{field.label}</Label>
        <Input
          id={field.name}
          type={field.type === "number" ? "number" : "text"}
          value={value ?? ""}
          min={field.min}
          max={field.max}
          step={field.step}
          placeholder={field.placeholder}
          onChange={(event) => updateField(
            field.name,
            field.type === "number" ? (event.target.value === "" ? "" : Number(event.target.value)) : event.target.value,
          )}
        />
      </div>
    )
  }

  return (
    <Card>
      <CardContent className="pt-6 space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold">Entrer les variables</h3>
            <p className="text-sm text-muted-foreground">Les champs changent selon le modèle sélectionné.</p>
          </div>
          <Button type="button" variant="outline" onClick={() => setFormData(model.example_values || {})}>
            Utiliser l'exemple
          </Button>
        </div>

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {model.input_fields.map(renderField)}
          </div>

          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={loading} className="min-w-40">
              {loading ? "Prédiction en cours..." : "Faire une prédiction"}
            </Button>
            <Button type="button" variant="ghost" onClick={() => setFormData({})}>
              Réinitialiser
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}