"use client"

import { useState } from "react"
import useSWR, { mutate } from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
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
import { Checkbox } from "@/components/ui/checkbox"
import { adminApi } from "@/lib/api"
import { toast } from "sonner"
import { Plus, MoreHorizontal, Pencil, Trash2, Loader2, Users } from "lucide-react"

const fetchUsers = () => adminApi.getUsers()
const fetchProducts = () => adminApi.getProducts()

interface UserForm {
  email: string
  name: string
  role: string
  organization: string
  products: number[]
}

const defaultForm: UserForm = {
  email: "",
  name: "",
  role: "client",
  organization: "",
  products: [],
}

export default function UsersManagementPage() {
  const { data: users, isLoading } = useSWR("admin-users", fetchUsers)
  const { data: products } = useSWR("admin-products", fetchProducts)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<any>(null)
  const [form, setForm] = useState<UserForm>(defaultForm)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  const handleOpenCreate = () => {
    setForm(defaultForm)
    setEditingUser(null)
    setIsDialogOpen(true)
  }

  const handleOpenEdit = (user: any) => {
    setForm({
      email: user.email,
      name: user.name,
      role: user.role,
      organization: user.organization,
      products: user.products || [],
    })
    setEditingUser(user)
    setIsDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      if (editingUser) {
        await adminApi.updateUser(editingUser.id, form)
        toast.success("Utilisateur modifié avec succès")
      } else {
        await adminApi.createUser(form)
        toast.success("Utilisateur créé avec succès")
      }
      mutate("admin-users")
      setIsDialogOpen(false)
      setForm(defaultForm)
      setEditingUser(null)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de l'opération")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (userId: number) => {
    try {
      await adminApi.deleteUser(userId)
      toast.success("Utilisateur supprimé")
      mutate("admin-users")
      setDeleteConfirm(null)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de la suppression")
    }
  }

  const toggleProduct = (productId: number) => {
    setForm((prev) => ({
      ...prev,
      products: prev.products.includes(productId)
        ? prev.products.filter((id) => id !== productId)
        : [...prev.products, productId],
    }))
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case "admin":
        return "bg-chart-1/10 text-chart-1 border-chart-1/20"
      case "directeur":
        return "bg-chart-2/10 text-chart-2 border-chart-2/20"
      case "client":
        return "bg-chart-3/10 text-chart-3 border-chart-3/20"
      default:
        return ""
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Gestion des Utilisateurs</h1>
              <p className="text-muted-foreground">
                Ajoutez, modifiez et gérez les accès des utilisateurs
              </p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={handleOpenCreate}>
                  <Plus className="w-4 h-4 mr-2" />
                  Nouvel Utilisateur
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>{editingUser ? "Modifier l'utilisateur" : "Nouvel utilisateur"}</DialogTitle>
                  <DialogDescription>
                    {editingUser ? "Modifiez les informations de l'utilisateur" : "Créez un nouveau compte utilisateur"}
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Nom complet</Label>
                    <Input
                      id="name"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      placeholder="Jean Dupont"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      placeholder="jean@exemple.com"
                      required
                      disabled={!!editingUser}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="organization">Organisation</Label>
                    <Input
                      id="organization"
                      value={form.organization}
                      onChange={(e) => setForm({ ...form, organization: e.target.value })}
                      placeholder="Ministère de..."
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role">Rôle</Label>
                    <Select value={form.role} onValueChange={(value) => setForm({ ...form, role: value })}>
                      <SelectTrigger>
                        <SelectValue placeholder="Sélectionner un rôle" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="client">Client</SelectItem>
                        <SelectItem value="admin">Administrateur</SelectItem>
                        <SelectItem value="directeur">Directeur</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {form.role === "client" && products && (
                    <div className="space-y-2">
                      <Label>Produits attribués</Label>
                      <div className="border rounded-lg p-3 space-y-2 max-h-40 overflow-y-auto">
                        {products.map((product: any) => (
                          <div key={product.id} className="flex items-center space-x-2">
                            <Checkbox
                              id={`product-${product.id}`}
                              checked={form.products.includes(product.id)}
                              onCheckedChange={() => toggleProduct(product.id)}
                            />
                            <label
                              htmlFor={`product-${product.id}`}
                              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                            >
                              {product.name}
                            </label>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        L&apos;attribution d&apos;un produit équivaut à un achat
                      </p>
                    </div>
                  )}

                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                      Annuler
                    </Button>
                    <Button type="submit" disabled={isSubmitting}>
                      {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                      {editingUser ? "Enregistrer" : "Créer"}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          <Card>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : users && users.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Utilisateur</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Organisation</TableHead>
                      <TableHead>Rôle</TableHead>
                      <TableHead>Produits</TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user: any) => (
                      <TableRow key={user.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-semibold text-primary">
                              {user.name.charAt(0).toUpperCase()}
                            </div>
                            <span className="font-medium">{user.name}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-muted-foreground">{user.email}</TableCell>
                        <TableCell>{user.organization}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={getRoleBadgeColor(user.role)}>
                            {user.role === "directeur" ? "Directeur" : user.role === "admin" ? "Admin" : "Client"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {user.products && user.products.length > 0 ? (
                            <span className="text-sm text-muted-foreground">
                              {user.products.length} produit(s)
                            </span>
                          ) : (
                            <span className="text-sm text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleOpenEdit(user)}>
                                <Pencil className="w-4 h-4 mr-2" />
                                Modifier
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() => setDeleteConfirm(user.id)}
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Supprimer
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="py-12 text-center">
                  <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Aucun utilisateur</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Delete Confirmation Dialog */}
          <Dialog open={deleteConfirm !== null} onOpenChange={() => setDeleteConfirm(null)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Confirmer la suppression</DialogTitle>
                <DialogDescription>
                  Êtes-vous sûr de vouloir supprimer cet utilisateur ? Cette action est irréversible.
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
