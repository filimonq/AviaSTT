import React from "react"

export function Card({ className, children }) {
  return (
    <div className={`${className} bg-white shadow-md rounded-lg`}>
      {children}
    </div>
  )
}

export function CardContent({ className, children }) {
  return (
    <div className={`${className} p-6`}>
      {children}
    </div>
  )
}