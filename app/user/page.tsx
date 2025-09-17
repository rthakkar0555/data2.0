"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { AppLayout } from "@/components/layout/app-layout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Search, Upload, FileText, Send, User, Bot, Loader2 } from "lucide-react"
import { apiService, type Model, type Company } from "@/lib/api"
import { toast } from "sonner"
import { ErrorBoundary } from "@/components/error-boundary"

export default function UserPage() {
  const [selectedCompany, setSelectedCompany] = useState("")
  const [selectedProduct, setSelectedProduct] = useState("")
  const [productCode, setProductCode] = useState("")
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadProductName, setUploadProductName] = useState("")
  const [uploadProductCode, setUploadProductCode] = useState("")
  const [uploadCompanyName, setUploadCompanyName] = useState("")
  const [query, setQuery] = useState("")
  const [showPdfDialog, setShowPdfDialog] = useState(false)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [currentChatMessages, setCurrentChatMessages] = useState<Array<{ type: "user" | "bot"; message: string }>>([])
  const [companies, setCompanies] = useState<string[]>([])
  const [models, setModels] = useState<Model[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isQuerying, setIsQuerying] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  // Load companies and models on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true)
        
        // Check if backend is available first
        try {
          await apiService.healthCheck()
        } catch (error) {
          console.error('Backend not available:', error)
          toast.error('Backend server is not running. Please start the backend server.')
          setIsLoading(false)
          return
        }
        
        const companiesData = await apiService.getCompanies()
        setCompanies(companiesData.companies || [])
        
        // Load models for all companies
        const allModels: Model[] = []
        for (const company of companiesData.companies || []) {
          try {
            const modelsData = await apiService.getModelsForCompany(company)
            allModels.push(...(modelsData.models || []))
          } catch (error) {
            console.error(`Failed to load models for ${company}:`, error)
          }
        }
        setModels(allModels)
      } catch (error) {
        console.error('Failed to load data:', error)
        toast.error('Failed to load data from backend. Please check if the backend server is running.')
        // Set empty arrays to prevent crashes
        setCompanies([])
        setModels([])
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])



  const handleCompanyChange = (value: string) => {
    console.log("Company selected:", value)
    setSelectedCompany(value)
    setSelectedProduct("") // Reset product when company changes
    setProductCode("") // Reset product code when company changes
  }

  const handleProductChange = (value: string) => {
    console.log("Product selected:", value, "for company:", selectedCompany)
    setSelectedProduct(value)
    // Auto-fill product code based on selected product from backend data
    const selectedModel = models.find(m => m.company_name === selectedCompany && m.product_name === value)
    if (selectedModel) {
      setProductCode(selectedModel.filename) // Using filename as product identifier
    }
  }

  const handleRetrieveManual = () => {
    console.log("Retrieving manual for:", selectedCompany, selectedProduct, productCode)
    setShowPdfDialog(false)
  }

  const handleUploadPdf = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!uploadFile) {
      toast.error('Please select a file to upload')
      return
    }

    if (!uploadCompanyName.trim()) {
      toast.error('Please enter a company name')
      return
    }

    // Validate file type
    if (uploadFile.type !== 'application/pdf') {
      toast.error('Please select a PDF file')
      return
    }

    // Validate file size (max 10MB)
    if (uploadFile.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB')
      return
    }

    try {
      setIsUploading(true)
      const response = await apiService.uploadPdf(
        uploadFile,
        uploadCompanyName,
        uploadProductName || undefined,
        uploadProductCode || undefined
      )
      
      toast.success(response.message || 'File uploaded successfully')
      
      // Refresh the data
      try {
        const companiesData = await apiService.getCompanies()
        setCompanies(companiesData.companies || [])
        
        // Load models for all companies
        const allModels: Model[] = []
        for (const company of companiesData.companies || []) {
          try {
            const modelsData = await apiService.getModelsForCompany(company)
            allModels.push(...(modelsData.models || []))
          } catch (error) {
            console.error(`Failed to load models for ${company}:`, error)
          }
        }
        setModels(allModels)
      } catch (error) {
        console.error('Failed to refresh data after upload:', error)
        toast.error('Upload successful but failed to refresh data')
      }
      
      // Reset form
      setUploadFile(null)
      setUploadProductName("")
      setUploadProductCode("")
      setUploadCompanyName("")
      setShowUploadDialog(false)
    } catch (error) {
      console.error('Upload failed:', error)
      let errorMessage = 'Upload failed'
      
      if (error instanceof Error) {
        if (error.message.includes('413')) {
          errorMessage = 'File too large. Please select a smaller file.'
        } else if (error.message.includes('400')) {
          errorMessage = 'Invalid file format or missing required information.'
        } else {
          errorMessage = error.message
        }
      }
      
      toast.error(errorMessage)
    } finally {
      setIsUploading(false)
    }
  }

  const handleSendQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      const newMessage = { type: "user" as const, message: query }
      setCurrentChatMessages((prev) => [...prev, newMessage])
      const currentQuery = query
      setQuery("")

      try {
        setIsQuerying(true)
        
        // Check if we have any models loaded
        if (models.length === 0) {
          const errorResponse = {
            type: "bot" as const,
            message: "No manuals are available. Please upload a PDF manual first or contact an administrator.",
          }
          setCurrentChatMessages((prev) => [...prev, errorResponse])
          toast.error('No manuals available')
          return
        }
        
        const response = await apiService.query({
          query: currentQuery,
          company_name: selectedCompany || undefined,
          product_code: productCode || undefined
        })
        
        const botResponse = {
          type: "bot" as const,
          message: response.response || "I received your query but couldn't generate a response.",
        }
        setCurrentChatMessages((prev) => [...prev, botResponse])
      } catch (error) {
        console.error('Query failed:', error)
        let errorMessage = "Sorry, I couldn't process your query. Please try again."
        
        if (error instanceof Error) {
          if (error.message.includes('No documents uploaded')) {
            errorMessage = "No manuals are available. Please upload a PDF manual first."
          } else if (error.message.includes('No relevant information')) {
            errorMessage = "I couldn't find relevant information in the available manuals for your query."
          } else {
            errorMessage = error.message
          }
        }
        
        const errorResponse = {
          type: "bot" as const,
          message: errorMessage,
        }
        setCurrentChatMessages((prev) => [...prev, errorResponse])
        toast.error('Failed to get response from AI')
      } finally {
        setIsQuerying(false)
      }
    }
  }

  const startNewChat = () => {
    setCurrentChatMessages([])
  }

  return (
    <ErrorBoundary>
      <AppLayout selectedValues={{
        companyName: selectedCompany,
        productName: selectedProduct,
        productCode: productCode
      }}>
        <div className="h-[calc(100vh-4rem)]">
        {/* Main Chat Area */}
        <div className="h-full bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col">
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-200">
            <h1 className="text-xl font-semibold text-gray-900">Manual Assistant</h1>
            <p className="text-sm text-gray-500">Ask questions about your manuals</p>
            <div className="mt-2 flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                isLoading ? 'bg-yellow-500' : 
                models.length > 0 ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className="text-xs text-gray-500">
                {isLoading ? 'Loading...' : 
                 models.length > 0 ? `${models.length} manuals available` : 
                 'No manuals available'}
              </span>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-5xl mx-auto space-y-6">
              {currentChatMessages.map((message, index) => (
                <div key={index} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`flex items-start space-x-3 max-w-3xl ${message.type === "user" ? "flex-row-reverse space-x-reverse" : ""}`}
                  >
                    <div
                      className={`p-2 rounded-full ${message.type === "user" ? "bg-black text-white" : "bg-gray-100 text-gray-700"}`}
                    >
                      {message.type === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                    </div>
                    <div
                      className={`p-4 rounded-lg ${message.type === "user" ? "bg-black text-white" : "bg-gray-50 text-gray-900"}`}
                    >
                      <p className="text-sm leading-relaxed">{message.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 border-t border-gray-200">
            <div className="max-w-5xl mx-auto">
              {/* Query Input */}
              <form onSubmit={handleSendQuery} className="flex gap-2 mb-4">
                <Textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={
                    isLoading ? "Loading manuals..." :
                    models.length === 0 ? "No manuals available. Please upload a PDF first." :
                    "Ask a question about your manual..."
                  }
                  className="flex-1 border-gray-300 focus:border-black focus:ring-black resize-none min-h-[50px]"
                  rows={2}
                  disabled={isLoading || models.length === 0}
                />
                <Button 
                  type="submit" 
                  disabled={isQuerying || isLoading || models.length === 0} 
                  className="bg-black text-white hover:bg-gray-800 px-4 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isQuerying ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </form>

              {/* Action Buttons at Bottom */}
              <div className="flex gap-2 justify-center">
                <Dialog open={showPdfDialog} onOpenChange={setShowPdfDialog}>
                  <DialogTrigger asChild>
                    <Button
                      variant="outline"
                      className="flex items-center gap-2 border-gray-300 hover:bg-gray-50 bg-transparent"
                    >
                      <Search className="h-4 w-4" />
                      Select PDF
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-md bg-white text-black">
                    <DialogHeader>
                      <DialogTitle>Select PDF Manual</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="company-select">Company Name</Label>
                        <Select value={selectedCompany} onValueChange={handleCompanyChange} disabled={isLoading}>
                          <SelectTrigger className="border-gray-300 focus:border-black focus:ring-black">
                            <SelectValue placeholder={isLoading ? "Loading companies..." : "Select a company"} />
                          </SelectTrigger>
                          <SelectContent className="bg-white">
                            {isLoading ? (
                              <SelectItem value="loading" disabled>
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                Loading companies...
                              </SelectItem>
                            ) : companies.length === 0 ? (
                              <SelectItem value="no-companies" disabled>
                                No companies available
                              </SelectItem>
                            ) : (
                              companies.map((company) => (
                                <SelectItem key={company} value={company}>
                                  {company}
                                </SelectItem>
                              ))
                            )}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="product-select">Product Name</Label>
                        <Select value={selectedProduct} onValueChange={handleProductChange} disabled={!selectedCompany || isLoading}>
                          <SelectTrigger className="border-gray-300 focus:border-black focus:ring-black">
                            <SelectValue placeholder={
                              isLoading ? "Loading..." : 
                              selectedCompany ? "Select a product" : "Select a company first"
                            } />
                          </SelectTrigger>
                          <SelectContent className="bg-white">
                            {selectedCompany && (() => {
                              const companyModels = models.filter(m => m.company_name === selectedCompany)
                              console.log("Filtering products for company:", selectedCompany, "Models:", companyModels)
                              return companyModels.length === 0 ? (
                                <SelectItem value="no-products" disabled>
                                  No products available for this company
                                </SelectItem>
                              ) : (
                                companyModels.map((model) => (
                                  <SelectItem key={model.product_name} value={model.product_name}>
                                    {model.product_name}
                                  </SelectItem>
                                ))
                              )
                            })()}
                            {!selectedCompany && (
                              <SelectItem value="select-company-first" disabled>
                                Please select a company first
                              </SelectItem>
                            )}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="product-code">Product Code (Optional)</Label>
                        <Input
                          id="product-code"
                          value={productCode}
                          onChange={(e) => setProductCode(e.target.value)}
                          placeholder="Product code will auto-fill"
                          className="border-gray-300 focus:border-black focus:ring-black"
                          readOnly
                        />
                      </div>
                      <Button onClick={handleRetrieveManual} className="w-full bg-black text-white hover:bg-gray-800">
                        <FileText className="mr-2 h-4 w-4" />
                        Load Manual
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>

                <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
                  <DialogTrigger asChild>
                    <Button
                      variant="outline"
                      className="flex items-center gap-2 border-gray-300 hover:bg-gray-50 bg-transparent"
                    >
                      <Upload className="h-4 w-4" />
                      Upload PDF
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-md bg-white text-black">
                    <DialogHeader>
                      <DialogTitle>Upload Your PDF Manual</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleUploadPdf} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="upload-company-name">Company Name</Label>
                        <Input
                          id="upload-company-name"
                          value={uploadCompanyName}
                          onChange={(e) => setUploadCompanyName(e.target.value)}
                          placeholder="Enter company name"
                          className="border-gray-300 focus:border-black focus:ring-black"
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="upload-file">PDF File</Label>
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-black transition-colors">
                          <input
                            id="upload-file"
                            type="file"
                            accept=".pdf"
                            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                            className="hidden"
                          />
                          <label htmlFor="upload-file" className="cursor-pointer">
                            <Upload className="mx-auto h-8 w-8 text-gray-400 mb-2" />
                            <p className="text-sm text-gray-600">
                              {uploadFile ? uploadFile.name : "Click to upload PDF"}
                            </p>
                          </label>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="upload-product-name">Product Name (Optional)</Label>
                        <Input
                          id="upload-product-name"
                          value={uploadProductName}
                          onChange={(e) => setUploadProductName(e.target.value)}
                          placeholder="Enter product name"
                          className="border-gray-300 focus:border-black focus:ring-black"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="upload-product-code">Product Code (Optional)</Label>
                        <Input
                          id="upload-product-code"
                          value={uploadProductCode}
                          onChange={(e) => setUploadProductCode(e.target.value)}
                          placeholder="Enter product code"
                          className="border-gray-300 focus:border-black focus:ring-black"
                        />
                      </div>
                      <Button type="submit" disabled={isUploading} className="w-full bg-black text-white hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed">
                        {isUploading ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Uploading...
                          </>
                        ) : (
                          'Upload and Process'
                        )}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
    </ErrorBoundary>
  )
}
