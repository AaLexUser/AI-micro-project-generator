import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import clsx from "clsx";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "relative overflow-hidden bg-primary text-primary-foreground hover:opacity-95",
        secondary: "bg-secondary text-secondary-foreground hover:opacity-90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        destructive: "bg-destructive text-destructive-foreground hover:opacity-90",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    React.AnchorHTMLAttributes<HTMLAnchorElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  href?: string;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild, href, children, ...props }, ref) => {
    const classes = clsx(buttonVariants({ variant, size }), className);
    if (href) {
      return (
        <a href={href} className={classes} {...(props as any)}>
          {children}
        </a>
      );
    }
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children as React.ReactElement, {
        className: clsx(classes, (children as any).props?.className),
      });
    }
    return (
      <button className={classes} ref={ref} {...props}>
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";


