/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: [
		"./index.html",
		"./src/**/*.{ts,tsx}",
	],
	theme: {
    	extend: {
    		colors: {
    			brand: {
    				'50': '#f0f9ff',
    				'100': '#e0f2fe',
    				'200': '#bae6fd',
    				'300': '#7dd3fc',
    				'400': '#38bdf8',
    				'500': '#0ea5e9',
    				'600': '#0284c7',
    				'700': '#0369a1',
    				'800': '#075985',
    				'900': '#0c4a6e',
    				'950': '#082f49',
    				DEFAULT: '#0ea5e9',
    				muted: '#e0f2fe'
    			},
    			purple: {
    				'50': '#faf5ff',
    				'100': '#f3e8ff',
    				'200': '#e9d5ff',
    				'300': '#d8b4fe',
    				'400': '#c084fc',
    				'500': '#a855f7',
    				'600': '#9333ea',
    				'700': '#7c3aed',
    				'800': '#6d28d9',
    				'900': '#581c87',
    				'950': '#3b0764',
    				DEFAULT: '#7c3aed',
    			},
    			cyan: {
    				'50': '#ecfeff',
    				'100': '#cffafe',
    				'200': '#a5f3fc',
    				'300': '#67e8f9',
    				'400': '#22d3ee',
    				'500': '#06b6d4',
    				'600': '#0891b2',
    				'700': '#0e7490',
    				'800': '#155e75',
    				'900': '#164e63',
    				'950': '#083344',
    				DEFAULT: '#06b6d4',
    			},
    			gray: {
    				'50': '#f9fafb',
    				'100': '#f3f4f6',
    				'200': '#e5e7eb',
    				'300': '#d1d5db',
    				'400': '#9ca3af',
    				'500': '#6b7280',
    				'600': '#4b5563',
    				'700': '#374151',
    				'800': '#1f2937',
    				'900': '#111827',
    				'950': '#030712'
    			},
    			background: 'hsl(var(--background))',
    			foreground: 'hsl(var(--foreground))',
    			card: {
    				DEFAULT: 'hsl(var(--card))',
    				foreground: 'hsl(var(--card-foreground))'
    			},
    			popover: {
    				DEFAULT: 'hsl(var(--popover))',
    				foreground: 'hsl(var(--popover-foreground))'
    			},
    			primary: {
    				DEFAULT: 'hsl(var(--primary))',
    				foreground: 'hsl(var(--primary-foreground))'
    			},
    			secondary: {
    				DEFAULT: 'hsl(var(--secondary))',
    				foreground: 'hsl(var(--secondary-foreground))'
    			},
    			muted: {
    				DEFAULT: 'hsl(var(--muted))',
    				foreground: 'hsl(var(--muted-foreground))'
    			},
    			accent: {
    				DEFAULT: 'hsl(var(--accent))',
    				foreground: 'hsl(var(--accent-foreground))'
    			},
    			destructive: {
    				DEFAULT: 'hsl(var(--destructive))',
    				foreground: 'hsl(var(--destructive-foreground))'
    			},
    			border: 'hsl(var(--border))',
    			input: 'hsl(var(--input))',
    			ring: 'hsl(var(--ring))',
    			chart: {
    				'1': 'hsl(var(--chart-1))',
    				'2': 'hsl(var(--chart-2))',
    				'3': 'hsl(var(--chart-3))',
    				'4': 'hsl(var(--chart-4))',
    				'5': 'hsl(var(--chart-5))'
    			}
    		},
    		boxShadow: {
    			card: '0 1px 3px 0 rgba(230, 113, 69, 0.1), 0 1px 2px 0 rgba(230, 113, 69, 0.06)',
    			'card-hover': '0 4px 6px -1px rgba(230, 113, 69, 0.15), 0 2px 4px -1px rgba(230, 113, 69, 0.1)',
    			'card-lg': '0 10px 15px -3px rgba(230, 113, 69, 0.15), 0 4px 6px -2px rgba(230, 113, 69, 0.1)',
    			glow: '0 0 30px rgba(230, 113, 69, 0.2), 0 0 60px rgba(230, 113, 69, 0.1)',
    			'primary': '0 4px 14px 0 rgba(230, 113, 69, 0.15)',
    			'purple': '0 4px 14px 0 rgba(124, 58, 237, 0.15)',
    			'cyan': '0 4px 14px 0 rgba(6, 182, 212, 0.15)'
    		},
    		animation: {
    			'fade-in': 'fadeIn 0.5s ease-in-out',
    			'slide-up': 'slideUp 0.3s ease-out',
    			'pulse-subtle': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
    		},
    		keyframes: {
    			fadeIn: {
    				'0%': {
    					opacity: '0'
    				},
    				'100%': {
    					opacity: '1'
    				}
    			},
    			slideUp: {
    				'0%': {
    					transform: 'translateY(10px)',
    					opacity: '0'
    				},
    				'100%': {
    					transform: 'translateY(0)',
    					opacity: '1'
    				}
    			}
    		},
    		typography: {
    			DEFAULT: {
    				css: {
    					color: 'hsl(230, 15%, 15%)',
    					maxWidth: 'none',
    					'h1, h2, h3, h4': {
    						color: 'hsl(230, 15%, 15%)',
    						fontWeight: '600'
    					},
    					'code': {
    						color: 'hsl(252, 83%, 57%)',
    						background: 'linear-gradient(to right, hsl(252, 83%, 57%, 0.1), hsl(199, 89%, 48%, 0.05))',
    						padding: '0.25rem 0.5rem',
    						borderRadius: '0.375rem',
    						fontSize: '0.875em',
    						border: '1px solid hsl(252, 83%, 57%, 0.2)',
    						fontWeight: '500'
    					},
    					'pre': {
    						background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
    						border: '1px solid hsl(252, 83%, 57%, 0.2)',
    						borderRadius: '0.75rem',
    						boxShadow: '0 4px 6px -1px rgba(14, 165, 233, 0.1), 0 2px 4px -1px rgba(124, 58, 237, 0.06)',
    					},
    					'pre code': {
    						backgroundColor: 'transparent',
    						color: 'inherit',
    						border: 'none',
    						background: 'transparent'
    					}
    				}
    			}
    		},
    		borderRadius: {
    			lg: 'var(--radius)',
    			md: 'calc(var(--radius) - 2px)',
    			sm: 'calc(var(--radius) - 4px)'
    		}
    	}
    },
	plugins: [
		require('@tailwindcss/typography'),
        require("tailwindcss-animate")
    ],
};
