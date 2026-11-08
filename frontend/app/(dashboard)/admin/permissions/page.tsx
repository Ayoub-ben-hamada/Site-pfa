"use client"

import { useEffect, useMemo, useState } from "react"
import useSWR from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { adminApi } from "@/lib/api"
import { toast } from "sonner"
import { ShieldCheck } from "lucide-react"

const fetchUsers = () => adminApi.getUsers()
const fetchProducts = () => adminApi.getProducts()
const AVAILABLE_FEATURES = ["download", "install", "update", "history"]

export default function PermissionsPage() {
  const { data: users } = useSWR("admin-users", fetchUsers)
  const { data: products } = useSWR("admin-products", fetchProducts)

  const [userId, setUserId] = useState<string>("")
  const [productId, setProductId] = useState<string>("")
  const [canView, setCanView] = useState(true)
  const [canUpdate, setCanUpdate] = useState(true)
  const [features, setFeatures] = useState<string[]>(AVAILABLE_FEATURES)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoadingPermission, setIsLoadingPermission] = useState(false)

  const clientUsers = useMemo(() => users?.filter((u: any) => u.role === "client") || [], [users])

  const selectedUser = useMemo(() => clientUsers.find((u: any) => String(u.id) === userId), [clientUsers, userId])

  useEffect(() => {
    if (!userId || !productId) return

    const loadPermission = async () => {
      setIsLoadingPermission(true)
      try {
        const current = await adminApi.getPermissions(Number(userId), Number(productId))
        setCanView(Boolean(current.can_view))
        setCanUpdate(Boolean(current.can_update))
        setFeatures(Array.isArray(current.allowed_features) ? current.allowed_features : [])
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Erreur lors du chargement des permissions")
      } finally {
        setIsLoadingPermission(false)
      }
    }

    loadPermission()
  }, [userId, productId])

  const handleSave = async () => {
    if (!userId || !productId) {
      toast.error("Sélectionnez un utilisateur et un produit")
      return
    }

    setIsSaving(true)
    try {
      await adminApi.updatePermissions({
        user_id: Number(userId),
        product_id: Number(productId),
        can_view: canView,
        can_update: canUpdate,
        allowed_features: features,
      })
      toast.success("Permissions mises à jour")
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de la mise à jour")
    } finally {
      setIsSaving(false)
    }
  }

  const toggleFeature = (feature: string) => {
    setFeatures((current) =>
      current.includes(feature)
        ? current.filter((item) => item !== feature)
        : [...current, feature]
    )
  }

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Gestion des Droits</h1>
          <p className="text-muted-foreground">Définissez les applications visibles et les fonctionnalités utilisables.</p>
        </div>

        <Card className="max-w-2xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5" />
              Droits utilisateur
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label>Utilisateur</Label>
              <Select value={userId} onValueChange={setUserId}>
                <SelectTrigger>
                  <SelectValue placeholder="Sélectionnez un utilisateur" />
                </SelectTrigger>
                <SelectContent>
                  {clientUsers.map((u: any) => (
                    <SelectItem key={u.id} value={String(u.id)}>
                      {u.name} ({u.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label>Produit</Label>
              <Select value={productId} onValueChange={setProductId}>
                <SelectTrigger>
                  <SelectValue placeholder="Sélectionnez un produit" />
                </SelectTrigger>
                <SelectContent>
                  {products?.map((p: any) => (
                    <SelectItem key={p.id} value={String(p.id)}>
                      {p.name} (v{p.latest_version})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-3">
              <Checkbox checked={canView} onCheckedChange={(v) => setCanView(Boolean(v))} id="can_view" />
              <Label htmlFor="can_view">Peut voir l'application</Label>
            </div>

            <div className="flex items-center gap-3">
              <Checkbox checked={canUpdate} onCheckedChange={(v) => setCanUpdate(Boolean(v))} id="can_update" />
              <Label htmlFor="can_update">Peut faire les mises à jour</Label>
            </div>

            <div className="grid gap-2">
              <Label>Fonctionnalités autorisées</Label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 rounded-lg border p-3">
                {AVAILABLE_FEATURES.map((feature) => (
                  <label key={feature} className="flex items-center gap-2 text-sm">
                    <Checkbox
                      checked={features.includes(feature)}
                      onCheckedChange={() => toggleFeature(feature)}
                      id={`feature-${feature}`}
                    />
                    <span className="capitalize">{feature}</span>
                  </label>
                ))}
              </div>
            </div>

            {selectedUser && (
              <div className="text-sm text-muted-foreground p-3 rounded-lg bg-muted/50">
                Utilisateur sélectionné: <span className="font-medium text-foreground">{selectedUser.name}</span>
              </div>
            )}

            <Button onClick={handleSave} disabled={isSaving || isLoadingPermission}>
              {isLoadingPermission ? "Chargement..." : isSaving ? "Enregistrement..." : "Enregistrer les permissions"}
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
