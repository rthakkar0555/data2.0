"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Menu, X, Settings, Users, Search, Upload, QrCode, FileText } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/contexts/AuthContext"

interface SidebarProps {
  className?: string
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

export function Sidebar({ 
  className, 
  selectedValues, 
  onSelectPDF, 
  onQRScan, 
  onUploadPDF, 
  onNewChat, 
  showNewChatButton 
}: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()
  const { isAdmin } = useAuth()

  const navigation = [
    ...(isAdmin ? [{
      name: "Admin Panel",
      href: "/admin",
      icon: Settings,
    }] : []),
    ...(!isAdmin ? [{
      name: "User Panel",
      href: "/user",
      icon: Users,
    }] : []),
  ]

  return (
    <>
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 md:hidden bg-black text-white hover:bg-gray-800"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </Button>

      {/* Sidebar */}
      <div
        className={cn(
          "fixed left-0 top-0 z-40 h-full w-64 bg-black text-white transform transition-transform duration-200 ease-in-out",
          isOpen ? "translate-x-0" : "-translate-x-full",
          "md:translate-x-0",
          className,
        )}
      >
        <div className="flex flex-col h-full">
          <div className="p-6">
            <h2 className="text-xl font-bold">Manual Base</h2>
          </div>

          <nav className="px-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                    isActive ? "bg-white text-black" : "text-white hover:bg-gray-800",
                  )}
                  onClick={() => setIsOpen(false)}
                >
                  <Icon className="mr-3 h-5 w-5" />
                  {item.name}
                  {isActive && <div className="ml-auto w-1 h-6 bg-black rounded-full" />}
                </Link>
              )
            })}
          </nav>

          {/* Action Buttons */}
          <div className="px-4 py-4 border-t border-gray-700">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Actions</h3>
            <div className="space-y-2">
              {showNewChatButton && onNewChat && (
                <Button
                  onClick={onNewChat}
                  className="w-full justify-start bg-gray-800 text-white hover:bg-gray-700 border border-gray-600"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  New Chat
                </Button>
              )}
              {onSelectPDF && (
                <Button
                  onClick={onSelectPDF}
                  className="w-full justify-start bg-gray-800 text-white hover:bg-gray-700 border border-gray-600"
                >
                  <Search className="h-4 w-4 mr-2" />
                  Select PDF
                </Button>
              )}
              {onQRScan && (
                <Button
                  onClick={onQRScan}
                  className="w-full justify-start bg-gray-800 text-white hover:bg-gray-700 border border-gray-600"
                >
                  <QrCode className="h-4 w-4 mr-2" />
                  QR Scan
                </Button>
              )}
              {onUploadPDF && (
                <Button
                  onClick={onUploadPDF}
                  className="w-full justify-start bg-gray-800 text-white hover:bg-gray-700 border border-gray-600"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Upload PDF
                </Button>
              )}
            </div>
          </div>

          {/* Selected Values Display - Only show for non-admin users */}
          {!isAdmin && (
            <div className="px-4 pb-4 border-t border-gray-700 pt-4 mt-auto">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Selected Manual</h3>
              {selectedValues && (selectedValues.companyName || selectedValues.productName || selectedValues.productCode) ? (
                <div className="space-y-2 text-xs">
                  {selectedValues.companyName && (
                    <div className="bg-green-900 border border-green-700 rounded px-3 py-2">
                      <div className="text-green-300">Company:</div>
                      <div className="text-white font-medium">{selectedValues.companyName}</div>
                    </div>
                  )}
                  {selectedValues.productName && (
                    <div className="bg-green-900 border border-green-700 rounded px-3 py-2">
                      <div className="text-green-300">Product:</div>
                      <div className="text-white font-medium">{selectedValues.productName}</div>
                    </div>
                  )}
                  {selectedValues.productCode && (
                    <div className="bg-green-900 border border-green-700 rounded px-3 py-2">
                      <div className="text-green-300">Code:</div>
                      <div className="text-white font-medium">{selectedValues.productCode}</div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-gray-500 text-xs italic">
                  No manual selected
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Overlay for mobile */}
      {isOpen && (
        <div className="fixed inset-0 z-30 bg-black bg-opacity-50 md:hidden" onClick={() => setIsOpen(false)} />
      )}
    </>
  )
}
