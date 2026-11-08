"use client"

import { useState } from "react"
import useSWR, { mutate } from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { adminApi } from "@/lib/api"
import { toast } from "sonner"
import { Plus, MoreHorizontal, Pencil, Trash2, Loader2, Package } from "lucide-react"

const fetchProducts = () => adminApi.getProducts()

interface ProductForm {
  name: string
  description: string
  latest_version: string
  category: string
}

const defaultForm: ProductForm = {
  name: "",
  description: "",
  latest_version: "1.0",
  category: "Administration",
}

const categories = ["Finance", "Administration", "Communication", "Social", "Technique"]

export default function ProductsManagementPage() {
  const { data: products, isLoading } = useSWR("admin-products", fetchProducts)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<any>(null)
  const [form, setForm] = useState<ProductForm>(defaultForm)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  const handleOpenCreate = () => {
    setForm(defaultForm)
    setEditingProduct(null)
    setIsDialogOpen(true)
  }

  const handleOpenEdit = (product: any) => {
    setForm({
      name: product.name,
      description: product.description,
      latest_version: product.latest_version,
      category: product.category,
    })
    setEditingProduct(product)
    setIsDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      if (editingProduct) {
        await adminApi.updateProduct(editingProduct.id, form)
        toast.success("Produit modifié avec succès")
      } else {
        await adminApi.createProduct(form)
        toast.success("Produit créé avec succès")
      }
      mutate("admin-products")
      setIsDialogOpen(false)
      setForm(defaultForm)
      setEditingProduct(null)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de l'opération")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (productId: number) => {
    try {
      await adminApi.deleteProduct(productId)
      toast.success("Produit supprimé")
      mutate("admin-products")
      setDeleteConfirm(null)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de la suppression")
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
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Catalogue Produits</h1>
              <p className="text-muted-foreground">
                Gérez les produits logiciels CNI disponibles
              </p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={handleOpenCreate}>
                  <Plus className="w-4 h-4 mr-2" />
                  Nouveau Produit
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>{editingProduct ? "Modifier le produit" : "Nouveau produit"}</DialogTitle>
                  <DialogDescription>
                    {editingProduct ? "Modifiez les informations du produit" : "Ajoutez un nouveau produit au catalogue"}
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Nom du produit</Label>
                    <Input
                      id="name"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      placeholder="Ex: MADANIA"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      value={form.description}
                      onChange={(e) => setForm({ ...form, description: e.target.value })}
                      placeholder="Description du produit..."
                      required
                      rows={3}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="version">Version</Label>
                      <Input
                        id="version"
                        value={form.latest_version}
                        onChange={(e) => setForm({ ...form, latest_version: e.target.value })}
                        placeholder="1.0"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="category">Catégorie</Label>
                      <Select value={form.category} onValueChange={(value) => setForm({ ...form, category: value })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Catégorie" />
                        </SelectTrigger>
                        <SelectContent>
                          {categories.map((cat) => (
                            <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                      Annuler
                    </Button>
                    <Button type="submit" disabled={isSubmitting}>
                      {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                      {editingProduct ? "Enregistrer" : "Créer"}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : products && products.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product: any) => (
                <Card key={product.id} className="overflow-hidden">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/60 rounded-xl flex items-center justify-center text-primary-foreground font-bold text-lg">
                          {product.name.charAt(0)}
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg">{product.name}</h3>
                          <Badge variant="outline" className={getCategoryColor(product.category)}>
                            {product.category}
                          </Badge>
                        </div>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleOpenEdit(product)}>
                            <Pencil className="w-4 h-4 mr-2" />
                            Modifier
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setDeleteConfirm(product.id)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Supprimer
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                    <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                      {product.description}
                    </p>
                    <div className="flex items-center justify-between pt-4 border-t">
                      <span className="text-sm text-muted-foreground">Version actuelle</span>
                      <span className="font-semibold">v{product.latest_version}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center">
                  <Package className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Aucun produit</h3>
                  <p className="text-muted-foreground">
                    Commencez par ajouter un produit au catalogue.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Delete Confirmation Dialog */}
          <Dialog open={deleteConfirm !== null} onOpenChange={() => setDeleteConfirm(null)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Confirmer la suppression</DialogTitle>
                <DialogDescription>
                  Êtes-vous sûr de vouloir supprimer ce produit ? Cette action est irréversible.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
                  Annuler
                </Button>
                <Button variant="destructive" onClick={() => deleteConfirm && handleDelete(deleteConfirm)}>
                  Supprimer
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </main>
    </div>
  )
}
