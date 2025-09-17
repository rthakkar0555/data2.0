"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Menu, X, Settings, Users } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/contexts/AuthContext"

interface SidebarProps {
  className?: string
  selectedValues?: {
    companyName?: string
    productName?: string
    productCode?: string
  }
}

export function Sidebar({ className, selectedValues }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()
  const { isAdmin } = useAuth()

  const navigation = [
    ...(isAdmin ? [{
      name: "Admin Panel",
      href: "/admin",
      icon: Settings,
    }] : []),
    {
      name: "User Panel",
      href: "/user",
      icon: Users,
    },
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

          {/* Selected Values Display */}
          {selectedValues && (selectedValues.companyName || selectedValues.productName || selectedValues.productCode) && (
            <div className="px-4 pb-4 border-t border-gray-700 mt-[12px] pt-[10px]">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Selected Manual</h3>
              <div className="space-y-2 text-xs">
                {selectedValues.companyName && (
                  <div className="bg-gray-800 rounded px-3 py-2">
                    <div className="text-gray-400">Company:</div>
                    <div className="text-white font-medium">{selectedValues.companyName}</div>
                  </div>
                )}
                {selectedValues.productName && (
                  <div className="bg-gray-800 rounded px-3 py-2">
                    <div className="text-gray-400">Product:</div>
                    <div className="text-white font-medium">{selectedValues.productName}</div>
                  </div>
                )}
                {selectedValues.productCode && (
                  <div className="bg-gray-800 rounded px-3 py-2">
                    <div className="text-gray-400">Code:</div>
                    <div className="text-white font-medium">{selectedValues.productCode}</div>
                  </div>
                )}
              </div>
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
