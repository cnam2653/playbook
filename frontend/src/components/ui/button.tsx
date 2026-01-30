import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#c8ff00]/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0a0f] disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-[#c8ff00] text-[#0a0a0f] font-semibold shadow-lg shadow-[#c8ff00]/20 hover:bg-[#d4ff33] hover:shadow-[#c8ff00]/30 active:scale-[0.98]",
        destructive:
          "bg-red-600/90 text-white shadow-lg shadow-red-600/20 hover:bg-red-600 hover:shadow-red-600/30",
        outline:
          "border border-zinc-700 bg-transparent text-zinc-300 hover:bg-zinc-800/50 hover:border-zinc-600 hover:text-white",
        secondary:
          "bg-zinc-800 text-zinc-300 shadow-sm hover:bg-zinc-700 hover:text-white",
        ghost:
          "text-zinc-400 hover:bg-zinc-800/50 hover:text-white",
        link:
          "text-[#c8ff00] underline-offset-4 hover:underline",
        electric:
          "relative bg-gradient-to-r from-[#c8ff00] to-[#00ff88] text-[#0a0a0f] font-semibold shadow-lg hover:shadow-[0_0_30px_rgba(200,255,0,0.4)] active:scale-[0.98]",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-8 rounded-md px-4 text-xs",
        lg: "h-12 rounded-lg px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
