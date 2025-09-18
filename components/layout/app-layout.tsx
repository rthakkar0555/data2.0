import type React from "react"
import { Sidebar } from "./sidebar"
import { Header } from "./header"

interface AppLayoutProps {
  children: React.ReactNode
  selectedValues?: {
    companyName?: string
    productName?: string
    productCode?: string
  }
  onSelectPDF?: () => void
  onQRScan?: () => void
  onUploadPDF?: () => void
  onNewChat?: () => void
  showNewChatButton?: boolean
}

export function AppLayout({ 
  children, 
  selectedValues, 
  onSelectPDF, 
  onQRScan, 
  onUploadPDF, 
  onNewChat, 
  showNewChatButton 
}: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-black">
      <Sidebar 
        selectedValues={selectedValues} 
        onSelectPDF={onSelectPDF}
        onQRScan={onQRScan}
        onUploadPDF={onUploadPDF}
        onNewChat={onNewChat}
        showNewChatButton={showNewChatButton}
      />
      <div className="md:ml-64">
        <Header />
        <main className="p-6">{children}</main>
        <footer className="border-t border-gray-800 p-4 text-center text-gray-500 text-sm">
          © 2024 Manual Base Retrieval System. All rights reserved.
        </footer>
      </div>
    </div>
  )
}
