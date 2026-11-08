"use client"

import useSWR from "swr"
import { AppSidebar } from "@/components/app-sidebar"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { clientApi } from "@/lib/api"
import { History, Loader2, CheckCircle2, XCircle } from "lucide-react"

const fetcher = () => clientApi.getInstallations()

export default function HistoryPage() {
  const { data: installations, isLoading } = useSWR("client-installations", fetcher)

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Historique des Installations</h1>
            <p className="text-muted-foreground">
              Consultez l&apos;historique de vos installations et mises à jour
            </p>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : installations && installations.length > 0 ? (
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Produit</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Statut</TableHead>
                      <TableHead>Durée</TableHead>
                      <TableHead>Mode</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {installations.map((install: any) => (
                      <TableRow key={install.id}>
                        <TableCell>
                          {new Date(install.date_installation).toLocaleDateString("fr-FR")}
                        </TableCell>
                        <TableCell className="font-medium">{install.Nom_produit}</TableCell>
                        <TableCell>v{install.version_produit}</TableCell>
                        <TableCell>
                          {install.installation_reussie === "oui" ? (
                            <Badge className="bg-success/10 text-success border-success/20">
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                              Réussie
                            </Badge>
                          ) : (
                            <Badge variant="destructive">
                              <XCircle className="w-3 h-3 mr-1" />
                              Échouée
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>{install.Duree_installation_minutes} min</TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {install.Mode_installation === "Télémaintenance" ? "À distance" : "Sur site"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center">
                  <History className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Aucun historique</h3>
                  <p className="text-muted-foreground">
                    Aucune installation n&apos;a été enregistrée pour le moment.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}
