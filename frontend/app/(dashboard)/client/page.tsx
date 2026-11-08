"use client"

import { useState } from "react"
import useSWR, { mutate } from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { clientApi } from "@/lib/api"
import { toast } from "sonner"
import {
  Package,
  Download,
  RefreshCw,
  CheckCircle2,
  ArrowUpCircle,
  Loader2,
  AlertCircle,
  Calendar,
  Info,
} from "lucide-react"

const fetcher = () => clientApi.getProducts()

export default function ClientPortalPage() {
  const { data: products, error, isLoading } = useSWR("client-products", fetcher)
  const [updatingProduct, setUpdatingProduct] = useState<number | null>(null)
  const [confirmDialog, setConfirmDialog] = useState<{ open: boolean; product: any | null }>({
    open: false,
    product: null,
  })

  const handleUpdate = async (product: any) => {
    setConfirmDialog({ open: false, product: null })
    setUpdatingProduct(product.id)
    
    try {
      await clientApi.updateProduct(product.id)
      toast.success(`${product.name} mis à jour vers la version ${product.latest_version}`)
      mutate("client-products")
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de la mise à jour")
    } finally {
      setUpdatingProduct(null)
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "Finance":
        return "bg-chart-1/10 text-chart-1 border-chart-1/20"
      case "Administration":
        return "bg-chart-2/10 text-chart-2 border-chart-2/20"
      case "Communication":
        return "bg-chart-3/10 text-chart-3 border-chart-3/20"
      case "Social":
        return "bg-chart-4/10 text-chart-4 border-chart-4/20"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Mes Applications</h1>
            <p className="text-muted-foreground">
              Gérez vos logiciels CNI installés et effectuez les mises à jour disponibles
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                    <Package className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{products?.length || 0}</p>
                    <p className="text-sm text-muted-foreground">Applications installées</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-success/10 rounded-xl flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6 text-success" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      {products?.filter((p: any) => !p.update_available).length || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">À jour</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-warning/10 rounded-xl flex items-center justify-center">
                    <ArrowUpCircle className="w-6 h-6 text-warning" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">
                      {products?.filter((p: any) => p.update_available).length || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">Mises à jour disponibles</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Products Grid */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : error ? (
            <Card>
              <CardContent className="py-12">
                <div className="text-center">
                  <AlertCircle className="w-12 h-12 text-destructive mx-auto mb-4" />
                  <p className="text-muted-foreground">Erreur lors du chargement des produits</p>
                </div>
              </CardContent>
            </Card>
          ) : products && products.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {products.map((product: any) => (
                <Card key={product.id} className="overflow-hidden">
                  <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/60 rounded-xl flex items-center justify-center text-primary-foreground font-bold text-lg">
                          {product.name.charAt(0)}
                        </div>
                        <div>
                          <CardTitle className="text-xl">{product.name}</CardTitle>
                          <Badge variant="outline" className={getCategoryColor(product.category)}>
                            {product.category}
                          </Badge>
                        </div>
                      </div>
                      {product.update_available && (
                        <Badge className="bg-warning text-warning-foreground">
                          Mise à jour disponible
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">{product.description}</p>
                    
                    <Separator />
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground mb-1">Version installée</p>
                        <p className="font-semibold flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-success" />
                          v{product.installed_version}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground mb-1">Dernière version</p>
                        <p className="font-semibold flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${product.update_available ? 'bg-warning' : 'bg-success'}`} />
                          v{product.latest_version}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Calendar className="w-4 h-4" />
                      <span>Installé le {new Date(product.install_date).toLocaleDateString("fr-FR")}</span>
                    </div>

                    {product.update_available && (
                      <Button
                        className="w-full"
                        onClick={() => setConfirmDialog({ open: true, product })}
                        disabled={updatingProduct === product.id}
                      >
                        {updatingProduct === product.id ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Mise à jour en cours...
                          </>
                        ) : (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Mettre à jour vers v{product.latest_version}
                          </>
                        )}
                      </Button>
                    )}
                    
                    {!product.update_available && (
                      <div className="flex items-center gap-2 text-sm text-success bg-success/10 px-4 py-2 rounded-lg">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Vous utilisez la dernière version</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center">
                  <Package className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Aucune application</h3>
                  <p className="text-muted-foreground">
                    Aucun produit ne vous a été attribué pour le moment.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onOpenChange={(open) => setConfirmDialog({ open, product: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmer la mise à jour</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir mettre à jour {confirmDialog.product?.name} vers la version {confirmDialog.product?.latest_version} ?
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-start gap-3 p-4 bg-muted rounded-lg">
            <Info className="w-5 h-5 text-primary mt-0.5" />
            <div className="text-sm">
              <p className="font-medium mb-1">Informations importantes</p>
              <ul className="text-muted-foreground space-y-1">
                <li>- La mise à jour sera effectuée automatiquement</li>
                <li>- Un redémarrage de l&apos;application peut être nécessaire</li>
                <li>- Vos données seront conservées</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDialog({ open: false, product: null })}>
              Annuler
            </Button>
            <Button onClick={() => confirmDialog.product && handleUpdate(confirmDialog.product)}>
              Confirmer la mise à jour
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
