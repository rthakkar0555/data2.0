"use client"

import React, { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Camera, X, CheckCircle, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'
import { BrowserMultiFormatReader } from '@zxing/library'

interface QRScannerProps {
  isOpen: boolean
  onClose: () => void
  onScanSuccess: (data: { company_name: string; product_name: string; product_code: string }) => void
}

interface QRData {
  company_name: string
  product_name: string
  product_code: string
}

export function QRScanner({ isOpen, onClose, onScanSuccess }: QRScannerProps) {
  const [isScanning, setIsScanning] = useState(false)
  const [scannedData, setScannedData] = useState<QRData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [debugMode, setDebugMode] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const readerRef = useRef<BrowserMultiFormatReader | null>(null)

  const startScanning = async () => {
    try {
      setError(null)
      setIsScanning(true)
      
      // Create new reader instance
      const reader = new BrowserMultiFormatReader()
      readerRef.current = reader
      
      // Get available video devices
      const videoInputDevices = await reader.listVideoInputDevices()
      console.log('Available video devices:', videoInputDevices)
      
      // Use the first available device (usually back camera on mobile)
      const selectedDevice = videoInputDevices[0]
      
      if (videoRef.current) {
        // Start decoding from video element
        reader.decodeFromVideoDevice(selectedDevice.deviceId, videoRef.current, (result, err) => {
          if (result) {
            console.log('QR Code detected:', result.getText())
            handleQRCodeDetected(result.getText())
          }
          if (err && !(err instanceof Error && err.name === 'NotFoundException')) {
            console.error('Decoding error:', err)
          }
        })
        
        // Start video stream
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            deviceId: selectedDevice.deviceId,
            facingMode: 'environment',
            width: { ideal: 1920 },
            height: { ideal: 1080 }
          } 
        })
        
        streamRef.current = stream
        videoRef.current.srcObject = stream
        videoRef.current.play()
        
        console.log('QR scanning started successfully')
      }
    } catch (err) {
      console.error('Error starting QR scanner:', err)
      setError('Unable to start camera. Please check permissions.')
      setIsScanning(false)
      toast.error('Camera access denied or not available')
    }
  }


  const stopScanning = () => {
    if (readerRef.current) {
      readerRef.current.reset()
      readerRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    setIsScanning(false)
    setScannedData(null)
    setError(null)
  }

  const handleClose = () => {
    stopScanning()
    onClose()
  }

  const simulateQRScan = () => {
    // For testing purposes - simulate scanning a QR code
    const mockQRData: QRData = {
      company_name: "try",
      product_name: "try",
      product_code: "MFL55318536.pdf"
    }
    
    setScannedData(mockQRData)
    setIsScanning(false)
    toast.success('QR code scanned successfully!')
  }


  const handleQRCodeDetected = (data: string) => {
    try {
      const parsedData = JSON.parse(data) as QRData
      
      // Validate the required fields
      if (!parsedData.company_name || !parsedData.product_name || !parsedData.product_code) {
        throw new Error('Invalid QR code format. Missing required fields.')
      }
      
      setScannedData(parsedData)
      setIsScanning(false)
      toast.success('QR code scanned successfully!')
    } catch (err) {
      console.error('Error parsing QR code:', err)
      setError('Invalid QR code format. Please scan a valid QR code.')
      toast.error('Invalid QR code format')
    }
  }

  const confirmScan = () => {
    if (scannedData) {
      onScanSuccess(scannedData)
      handleClose()
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (readerRef.current) {
        readerRef.current.reset()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-md bg-white text-black">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Camera className="h-5 w-5" />
            QR Code Scanner
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {!isScanning && !scannedData && (
            <div className="text-center space-y-4">
              <div className="bg-gray-100 rounded-lg p-8">
                <Camera className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-sm text-gray-600 mb-4">
                  Scan a QR code containing product information
                </p>
              
                <Button 
                  onClick={startScanning}
                  className="w-full bg-black text-white hover:bg-gray-800"
                >
                  Start Camera
                </Button>
                <div className="space-y-2">
                  {/* <Button 
                    onClick={simulateQRScan}
                    variant="outline"
                    className="w-full border-gray-300 hover:bg-gray-50"
                  >
                    Simulate Scan (Test)
                  </Button> */}
                  {/* <Button 
                    onClick={() => setDebugMode(!debugMode)}
                    variant="outline"
                    className="w-full border-gray-300 hover:bg-gray-50"
                  >
                    {debugMode ? 'Hide Debug' : 'Show Debug'}
                  </Button> */}
                </div>
              </div>
            </div>
          )}

          {isScanning && (
            <div className="space-y-4">
              <div className="relative bg-black rounded-lg overflow-hidden">
                <video
                  ref={videoRef}
                  className="w-full h-64 object-cover scale-x-[-1]"
                  playsInline
                  muted
                />
                <div className="absolute inset-0 border-2 border-white border-dashed m-4 rounded-lg pointer-events-none">
                  <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                    <div className="w-12 h-12 border-2 border-white rounded-lg animate-pulse"></div>
                  </div>
                  <div className="absolute top-4 left-4 text-white text-xs bg-black bg-opacity-50 px-2 py-1 rounded">
                    Scanning...
                  </div>
                </div>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-2">Point camera at QR code</p>
                {debugMode && (
                  <div className="bg-gray-100 p-2 rounded text-xs text-left mb-2">
                    <p>Video: {videoRef.current?.videoWidth}x{videoRef.current?.videoHeight}</p>
                    <p>Reader: {readerRef.current ? 'Active' : 'Inactive'}</p>
                    <p>Scanning: {isScanning ? 'Active' : 'Inactive'}</p>
                    <p>Stream: {streamRef.current ? 'Connected' : 'Disconnected'}</p>
                  </div>
                )}
                <Button 
                  onClick={stopScanning}
                  variant="outline"
                  className="border-gray-300 hover:bg-gray-50"
                >
                  Stop Scanning
                </Button>
              </div>
            </div>
          )}

          {scannedData && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="font-medium text-green-800">QR Code Scanned Successfully!</span>
                </div>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Company:</span>
                    <span className="ml-2 text-gray-900">{scannedData.company_name}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Product:</span>
                    <span className="ml-2 text-gray-900">{scannedData.product_name}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Product Code:</span>
                    <span className="ml-2 text-gray-900">{scannedData.product_code}</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <Button 
                  onClick={confirmScan}
                  className="flex-1 bg-black text-white hover:bg-gray-800"
                >
                  Use This Data
                </Button>
                <Button 
                  onClick={() => {
                    setScannedData(null)
                    setError(null)
                  }}
                  variant="outline"
                  className="border-gray-300 hover:bg-gray-50"
                >
                  Scan Again
                </Button>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <span className="font-medium text-red-800">Error</span>
              </div>
              <p className="text-sm text-red-700">{error}</p>
              <Button 
                onClick={() => {
                  setError(null)
                  setScannedData(null)
                }}
                variant="outline"
                className="mt-2 border-red-300 hover:bg-red-50 text-red-700"
              >
                Try Again
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
