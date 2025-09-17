"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { AppLayout } from "@/components/layout/app-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { FileText, MessageSquare, BarChart3, Eye, Upload, Search, Edit, Trash2, Loader2 } from "lucide-react"
import { apiService, type Model, type Company } from "@/lib/api"
import { toast } from "sonner"
import { ErrorBoundary } from "@/components/error-boundary"

export default function AdminPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [companyName, setCompanyName] = useState("")
  const [productName, setProductName] = useState("")
  const [productCode, setProductCode] = useState("")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [companies, setCompanies] = useState<string[]>([])
  const [models, setModels] = useState<Model[]>([])
  const [selectedCompany, setSelectedCompany] = useState("")
  const [isLoading, setIsLoading] = useState(true)

  // Load companies and models on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true)
        const companiesData = await apiService.getCompanies()
        setCompanies(companiesData.companies)
        
        // Load models for all companies
        const allModels: Model[] = []
        for (const company of companiesData.companies) {
          try {
            const modelsData = await apiService.getModelsForCompany(company)
            allModels.push(...modelsData.models)
          } catch (error) {
            console.error(`Failed to load models for ${company}:`, error)
          }
        }
        setModels(allModels)
      } catch (error) {
        console.error('Failed to load data:', error)
        toast.error('Failed to load data from backend')
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  // Mock data for user queries
  const userQueries = [
    {
      id: 1,
      userId: "user123",
      query: "What is the product code for Widget A?",
      timestamp: "2024-01-15 10:30",
      response: "The code is WA001",
    },
    {
      id: 2,
      userId: "user456",
      query: "How to install Widget B?",
      timestamp: "2024-01-15 09:15",
      response: "Please refer to section 3.2",
    },
    {
      id: 3,
      userId: "user789",
      query: "Warranty information for Gadget X?",
      timestamp: "2024-01-14 16:45",
      response: "2-year warranty included",
    },
  ]

  const filteredModels = models.filter(
    (model) =>
      model.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      model.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      model.filename.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedFile) {
      toast.error('Please select a file to upload')
      return
    }

    if (!companyName.trim()) {
      toast.error('Please enter a company name')
      return
    }

    try {
      setIsUploading(true)
      const response = await apiService.uploadPdf(
        selectedFile,
        companyName,
        productName || undefined,
        productCode || undefined
      )
      
      toast.success(response.message)
      
      // Refresh the data
      const companiesData = await apiService.getCompanies()
      setCompanies(companiesData.companies)
      
      // Load models for all companies
      const allModels: Model[] = []
      for (const company of companiesData.companies) {
        try {
          const modelsData = await apiService.getModelsForCompany(company)
          allModels.push(...modelsData.models)
        } catch (error) {
          console.error(`Failed to load models for ${company}:`, error)
        }
      }
      setModels(allModels)
      
      // Reset form
      setCompanyName("")
      setProductName("")
      setProductCode("")
      setSelectedFile(null)
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error(error instanceof Error ? error.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDeleteManual = async (productName: string, productCode: string) => {
    try {
      const response = await apiService.deleteManual(productName, productCode)
      toast.success(response.message)
      
      // Refresh the data
      const companiesData = await apiService.getCompanies()
      setCompanies(companiesData.companies)
      
      // Load models for all companies
      const allModels: Model[] = []
      for (const company of companiesData.companies) {
        try {
          const modelsData = await apiService.getModelsForCompany(company)
          allModels.push(...modelsData.models)
        } catch (error) {
          console.error(`Failed to load models for ${company}:`, error)
        }
      }
      setModels(allModels)
    } catch (error) {
      console.error('Delete failed:', error)
      toast.error(error instanceof Error ? error.message : 'Delete failed')
    }
  }

  return (
    <ErrorBoundary>
      <AppLayout selectedValues={{
        companyName: companyName,
        productName: productName,
        productCode: productCode
      }}>
        <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Admin Dashboard</h1>
          <p className="text-gray-400">Overview of system metrics and activity</p>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-white text-black shadow-[0_2px_4px_rgba(255,255,255,0.1)]">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Manuals Uploaded</CardTitle>
              <FileText className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : models.length}</div>
              <p className="text-xs text-gray-600">Active documents</p>
            </CardContent>
          </Card>

          <Card className="bg-white text-black shadow-[0_2px_4px_rgba(255,255,255,0.1)]">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Companies</CardTitle>
              <MessageSquare className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : companies.length}</div>
              <p className="text-xs text-gray-600">Registered companies</p>
            </CardContent>
          </Card>

          <Card className="bg-white text-black shadow-[0_2px_4px_rgba(255,255,255,0.1)]">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Data Insights</CardTitle>
              <BarChart3 className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-sm font-medium mb-2">Top Products:</div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Widget A</span>
                  <span>20%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1">
                  <div className="bg-black h-1 rounded-full" style={{ width: "20%" }}></div>
                </div>
                <div className="flex justify-between text-xs">
                  <span>Widget B</span>
                  <span>15%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1">
                  <div className="bg-black h-1 rounded-full" style={{ width: "15%" }}></div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Upload Manual Section */}
        <Card className="bg-white text-black shadow-[0_2px_4px_rgba(255,255,255,0.1)]">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Upload className="mr-2 h-5 w-5" />
              Upload Manual
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleFileUpload} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="companyName">Company Name</Label>
                  <Input
                    id="companyName"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="Enter company name"
                    className="border-gray-300 focus:border-black focus:ring-black"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="productName">Product Name</Label>
                  <Input
                    id="productName"
                    value={productName}
                    onChange={(e) => setProductName(e.target.value)}
                    placeholder="Enter product name"
                    className="border-gray-300 focus:border-black focus:ring-black"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="productCode">Product Code</Label>
                  <Input
                    id="productCode"
                    value={productCode}
                    onChange={(e) => setProductCode(e.target.value)}
                    placeholder="Enter product code"
                    className="border-gray-300 focus:border-black focus:ring-black"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="file">PDF File</Label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-black transition-colors">
                  <input
                    id="file"
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                  <label htmlFor="file" className="cursor-pointer">
                    <Upload className="mx-auto h-12 w-12 text-gray-400 mb-2" />
                    <p className="text-sm text-gray-600">
                      {selectedFile ? selectedFile.name : "Drop PDF here or click to browse"}
                    </p>
                  </label>
                </div>
              </div>
              <Button
                type="submit"
                disabled={isUploading}
                className="bg-black text-white hover:bg-gray-800 hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  'Upload Manual'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Manuals Table */}
        <Card className="bg-white text-black shadow-[0_2px_4px_rgba(255,255,255,0.1)]">
          <CardHeader>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <CardTitle>Uploaded Manuals</CardTitle>
              <div className="flex items-center space-x-2">
                <Search className="h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by company, name or code..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-64 border-gray-300 focus:border-black focus:ring-black"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company Name</TableHead>
                  <TableHead>Product Name</TableHead>
                  <TableHead>Product Code</TableHead>
                  <TableHead>Upload Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                      <p className="mt-2 text-gray-500">Loading manuals...</p>
                    </TableCell>
                  </TableRow>
                ) : filteredModels.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                      No manuals found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredModels.map((model) => (
                    <TableRow key={model._id}>
                      <TableCell className="font-medium">{model.company_name}</TableCell>
                      <TableCell>{model.product_name}</TableCell>
                      <TableCell>{model.filename}</TableCell>
                      <TableCell>{new Date().toLocaleDateString()}</TableCell>
                      <TableCell>
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                          Active
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button variant="ghost" size="sm" className="hover:bg-gray-100">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="hover:bg-red-100 hover:text-red-600"
                            onClick={() => handleDeleteManual(model.product_name, model.filename)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-4">
          <Dialog>
            <DialogTrigger asChild>
              <Button className="bg-white text-black hover:bg-gray-100 hover:scale-105 transition-transform">
                <Eye className="mr-2 h-4 w-4" />
                View User Queries Log
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl bg-white text-black">
              <DialogHeader>
                <DialogTitle>User Queries Log</DialogTitle>
              </DialogHeader>
              <div className="max-h-96 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>User ID</TableHead>
                      <TableHead>Query Text</TableHead>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Response Summary</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {userQueries.map((query) => (
                      <TableRow key={query.id}>
                        <TableCell>{query.userId}</TableCell>
                        <TableCell className="max-w-xs truncate">{query.query}</TableCell>
                        <TableCell>{query.timestamp}</TableCell>
                        <TableCell className="max-w-xs truncate">{query.response}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </AppLayout>
    </ErrorBoundary>
  )
}
