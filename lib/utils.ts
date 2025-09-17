import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Utility function to extract clean text from markdown content for copying
export function extractCleanText(markdownContent: string): string {
  // Remove markdown formatting while preserving structure
  let cleanText = markdownContent
  
  // Remove markdown headers
  cleanText = cleanText.replace(/^#{1,6}\s+/gm, '')
  
  // Remove bold/italic formatting
  cleanText = cleanText.replace(/\*\*(.*?)\*\*/g, '$1')
  cleanText = cleanText.replace(/\*(.*?)\*/g, '$1')
  
  // Remove code blocks but keep the content
  cleanText = cleanText.replace(/```[\s\S]*?```/g, (match) => {
    return match.replace(/```/g, '').trim()
  })
  
  // Remove inline code formatting
  cleanText = cleanText.replace(/`([^`]+)`/g, '$1')
  
  // Remove links but keep the text
  cleanText = cleanText.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
  
  // Remove blockquotes formatting
  cleanText = cleanText.replace(/^>\s*/gm, '')
  
  // Clean up multiple newlines
  cleanText = cleanText.replace(/\n{3,}/g, '\n\n')
  
  return cleanText.trim()
}
