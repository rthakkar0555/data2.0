"use client"

import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { LogOut } from "lucide-react"

export function Header() {
  const router = useRouter()

  const handleLogout = () => {
    router.push("/login")
  }

  return (
    <header className="h-16 bg-black text-white border-b border-gray-800 flex items-center justify-between px-6">
      <h1 className="text-xl font-bold">Manual Base Retrieval System</h1>

      <div className="flex items-center space-x-4">
        <Avatar className="h-8 w-8 bg-white text-black">
          <AvatarFallback>U</AvatarFallback>
        </Avatar>
        <Button variant="ghost" size="sm" onClick={handleLogout} className="text-white hover:bg-gray-800">
          <LogOut className="h-4 w-4 mr-2" />
          Logout
        </Button>
      </div>
    </header>
  )
}
