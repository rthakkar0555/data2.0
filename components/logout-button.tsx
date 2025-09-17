"use client"

import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/contexts/AuthContext"

export function LogoutButton() {
  const router = useRouter()
  const { logout } = useAuth()

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  return (
    <Button
      onClick={handleLogout}
      variant="outline"
      className="border-red-300 text-red-700 hover:bg-red-50 hover:border-red-400"
    >
      Logout
    </Button>
  )
}
