"use client"

import React, { useState } from 'react'
import QRCode from 'qrcode'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Download, Copy } from 'lucide-react'
import { toast } from 'sonner'

interface QRGeneratorProps {
  isOpen: boolean
  onClose: () => void
}

export function QRGenerator({ isOpen, onClose }: QRGeneratorProps) {
  const [companyName, setCompanyName] = useState('try')
  const [productName, setProductName] = useState('try')
  const [productCode, setProductCode] = useState('MFL55318536.pdf')
  const [qrCodeDataUrl, setQrCodeDataUrl] = useState<string>('')

  const generateQRCode = async () => {
    try {
      const data = {
        company_name: companyName,
        product_name: productName,
        product_code: productCode
      }
      
      const jsonString = JSON.stringify(data)
      const qrCodeUrl = await QRCode.toDataURL(jsonString, {
        width: 300,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF'
        }
      })
      
      setQrCodeDataUrl(qrCodeUrl)
      toast.success('QR code generated successfully!')
    } catch (error) {
      console.error('Error generating QR code:', error)
      toast.error('Failed to generate QR code')
    }
  }

  const downloadQRCode = () => {
    if (qrCodeDataUrl) {
      const link = document.createElement('a')
      link.download = `qr-code-${productCode}.png`
      link.href = qrCodeDataUrl
      link.click()
      toast.success('QR code downloaded!')
    }
  }

  const copyQRData = () => {
    const data = {
      company_name: companyName,
      product_name: productName,
      product_code: productCode
    }
    
    navigator.clipboard.writeText(JSON.stringify(data))
    toast.success('QR data copied to clipboard!')
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md bg-white text-black">
        <DialogHeader>
          <DialogTitle>Generate Test QR Code</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="company-name">Company Name</Label>
            <Input
              id="company-name"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Enter company name"
              className="border-gray-300 focus:border-black focus:ring-black"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="product-name">Product Name</Label>
            <Input
              id="product-name"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="Enter product name"
              className="border-gray-300 focus:border-black focus:ring-black"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="product-code">Product Code</Label>
            <Input
              id="product-code"
              value={productCode}
              onChange={(e) => setProductCode(e.target.value)}
              placeholder="Enter product code"
              className="border-gray-300 focus:border-black focus:ring-black"
            />
          </div>
          
          <Button 
            onClick={generateQRCode}
            className="w-full bg-black text-white hover:bg-gray-800"
          >
            Generate QR Code
          </Button>
          
          {qrCodeDataUrl && (
            <div className="space-y-4">
              <div className="text-center">
                <img 
                  src={qrCodeDataUrl} 
                  alt="Generated QR Code" 
                  className="mx-auto border border-gray-200 rounded-lg"
                />
              </div>
              
              <div className="flex gap-2">
                <Button 
                  onClick={downloadQRCode}
                  variant="outline"
                  className="flex-1 border-gray-300 hover:bg-gray-50"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
                <Button 
                  onClick={copyQRData}
                  variant="outline"
                  className="flex-1 border-gray-300 hover:bg-gray-50"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copy Data
                </Button>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-xs text-gray-600 mb-2">QR Code Data:</p>
                <code className="text-xs text-gray-800 break-all">
                  {JSON.stringify({ company_name: companyName, product_name: productName, product_code: productCode }, null, 2)}
                </code>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
