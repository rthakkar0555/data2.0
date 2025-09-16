"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const router = useRouter()

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    // Simple placeholder logic - redirect to admin for demo
    if (email.includes("admin")) {
      router.push("/admin")
    } else {
      router.push("/user")
    }
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-white text-black shadow-[0_2px_4px_rgba(255,255,255,0.1)]">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">Login to Manual Base</CardTitle>
          <CardDescription className="text-gray-600">Enter your credentials to access the system</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="border-gray-300 focus:border-black focus:ring-black"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="border-gray-300 focus:border-black focus:ring-black"
                required
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-black text-white hover:bg-gray-800 hover:scale-105 transition-transform"
            >
              Sign In
            </Button>
          </form>
          <div className="mt-6 text-center space-y-2">
            <a href="#" className="text-gray-500 hover:text-gray-700 underline text-sm">
              Forgot Password?
            </a>
            <br />
            <a href="#" className="text-gray-500 hover:text-gray-700 underline text-sm">
              Sign Up
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
