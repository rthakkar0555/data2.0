import React, { ReactNode } from "react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

// Markdown component props type
type MdComponentProps = {
  className?: string
  children?: ReactNode
  [key: string]: any
}

// Custom markdown components for manual responses
export const markdownComponents = {
  h1: ({ className, children, ...props }: MdComponentProps) => (
    <h1 className={cn("text-2xl md:text-3xl font-bold mt-6 mb-5 text-gray-900 border-b-2 border-gray-300 pb-3", className)} {...props}>
      {children}
    </h1>
  ),
  h2: ({ className, children, ...props }: MdComponentProps) => (
    <h2 className={cn("text-xl md:text-2xl font-bold mt-6 mb-4 text-gray-900 border-b border-gray-200 pb-2", className)} {...props}>
      {children}
    </h2>
  ),
  h3: ({ className, children, ...props }: MdComponentProps) => (
    <h3 className={cn("text-lg md:text-xl font-bold mt-5 mb-3 text-gray-900", className)} {...props}>
      {children}
    </h3>
  ),
  h4: ({ className, children, ...props }: MdComponentProps) => (
    <h4 className={cn("text-base md:text-lg font-bold mt-4 mb-2 text-gray-900", className)} {...props}>
      {children}
    </h4>
  ),
  p: ({ className, children, ...props }: MdComponentProps) => {
    const content = children?.toString() || ""
    
    // Check if this paragraph contains a citation
    if (content.includes('[src:') && content.includes('pdf_uri=')) {
      return (
        <div className="my-5 p-4 bg-blue-50 border border-blue-200 rounded-lg shadow-sm">
          <div className="flex items-start gap-3">
            <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-300 text-xs flex-shrink-0">
              📖 Source
            </Badge>
            <div className="text-sm text-blue-700 font-mono break-all">
              {children}
            </div>
          </div>
        </div>
      )
    }
    
    return (
      <p className={cn("mb-4 leading-relaxed text-gray-700 text-sm md:text-base", className)} {...props}>
        {children}
      </p>
    )
  },
  a: ({ className, children, href, ...props }: MdComponentProps) => (
    <a
      className={cn("text-blue-600 hover:text-blue-800 underline font-medium", className)}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </a>
  ),
  ul: ({ className, children, ...props }: MdComponentProps) => (
    <ul className={cn("list-disc pl-6 mb-5 text-gray-700 space-y-2 text-sm md:text-base", className)} {...props}>
      {children}
    </ul>
  ),
  ol: ({ className, children, ...props }: MdComponentProps) => (
    <ol className={cn("list-decimal pl-6 mb-5 text-gray-700 space-y-2 text-sm md:text-base", className)} {...props}>
      {children}
    </ol>
  ),
  li: ({ className, children, ...props }: MdComponentProps) => (
    <li className={cn("mb-2 text-gray-700 leading-relaxed", className)} {...props}>
      {children}
    </li>
  ),
  blockquote: ({ className, children, ...props }: MdComponentProps) => {
    const content = children?.toString() || ""
    const isSafetyWarning = content.toLowerCase().includes('safety') || content.toLowerCase().includes('warning')
    const isImportant = content.toLowerCase().includes('important') || content.toLowerCase().includes('note')
    
    if (isSafetyWarning) {
      return (
        <div className="my-5 p-4 bg-red-50 border-l-4 border-red-400 rounded-r-lg shadow-sm">
          <div className="flex items-start gap-3">
            <Badge variant="destructive" className="bg-red-100 text-red-800 border-red-300 text-xs flex-shrink-0">
              ⚠️ Safety Warning
            </Badge>
            <div className="text-sm text-red-700 font-medium leading-relaxed">
              {children}
            </div>
          </div>
        </div>
      )
    }
    
    if (isImportant) {
      return (
        <div className="my-5 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg shadow-sm">
          <div className="flex items-start gap-3">
            <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-300 text-xs flex-shrink-0">
              💡 Important
            </Badge>
            <div className="text-sm text-yellow-700 font-medium leading-relaxed">
              {children}
            </div>
          </div>
        </div>
      )
    }
    
    return (
      <blockquote
        className={cn(
          "border-l-4 border-blue-400 pl-4 italic my-4 text-sm text-gray-600 bg-blue-50 rounded-r-lg py-2",
          className
        )}
        {...props}
      >
        {children}
      </blockquote>
    )
  },
  code: ({ className, children, ...props }: MdComponentProps) => (
    <code
      className={cn(
        "bg-gray-100 rounded px-1.5 py-0.5 font-mono text-sm text-gray-800 border border-gray-200",
        className
      )}
      {...props}
    >
      {children}
    </code>
  ),
  pre: ({ className, children, ...props }: MdComponentProps) => (
    <pre
      className={cn(
        "bg-gray-900 p-4 md:p-6 rounded-lg overflow-x-auto font-mono text-sm my-5 text-gray-100 border border-gray-700 shadow-sm",
        className
      )}
      {...props}
    >
      {children}
    </pre>
  ),
  hr: ({ className, ...props }: MdComponentProps) => (
    <hr className={cn("border-gray-300 my-6", className)} {...props} />
  ),
  table: ({ className, children, ...props }: MdComponentProps) => (
    <div className="my-5 overflow-x-auto shadow-sm rounded-lg border border-gray-200">
      <table className={cn("border-collapse w-full", className)} {...props}>
        {children}
      </table>
    </div>
  ),
  th: ({ className, children, ...props }: MdComponentProps) => (
    <th
      className={cn(
        "border border-gray-300 px-4 py-3 text-left font-bold text-gray-900 bg-gray-100 text-sm md:text-base",
        className
      )}
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ className, children, ...props }: MdComponentProps) => (
    <td
      className={cn("border border-gray-300 px-4 py-3 text-gray-700 text-sm md:text-base", className)}
      {...props}
    >
      {children}
    </td>
  ),
  strong: ({ className, children, ...props }: MdComponentProps) => (
    <strong className={cn("font-bold text-gray-900", className)} {...props}>
      {children}
    </strong>
  ),
  em: ({ className, children, ...props }: MdComponentProps) => (
    <em className={cn("italic text-gray-700", className)} {...props}>
      {children}
    </em>
  ),
}

// Special component for citations
export const CitationComponent = ({ children }: { children: ReactNode }) => (
  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
    <div className="flex items-start gap-2">
      <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-300 text-xs">
        📖 Source
      </Badge>
      <div className="text-sm text-blue-700 font-mono">
        {children}
      </div>
    </div>
  </div>
)

// Component for safety warnings
export const SafetyWarningComponent = ({ children }: { children: ReactNode }) => (
  <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-400 rounded-r-lg">
    <div className="flex items-start gap-2">
      <Badge variant="destructive" className="bg-red-100 text-red-800 border-red-300 text-xs">
        ⚠️ Safety Warning
      </Badge>
      <div className="text-sm text-red-700 font-medium">
        {children}
      </div>
    </div>
  </div>
)

// Component for important notes
export const ImportantNoteComponent = ({ children }: { children: ReactNode }) => (
  <div className="mt-4 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg">
    <div className="flex items-start gap-2">
      <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-300 text-xs">
        💡 Important
      </Badge>
      <div className="text-sm text-yellow-700 font-medium">
        {children}
      </div>
    </div>
  </div>
)
