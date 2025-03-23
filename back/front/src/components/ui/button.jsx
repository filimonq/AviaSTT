import React from "react"

export function Button({ variant, size, className, onClick, children }) {
  return (
    <button
      className={`${className} ${variant === "destructive" ? "bg-red-500" : "bg-blue-500"} ${size === "icon" ? "p-2" : "p-4"}`}
      onClick={onClick}
    >
      {children}
    </button>
  )
}