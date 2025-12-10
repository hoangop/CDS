/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  safelist: [
    'bg-cyan-600',
    'bg-gray-50',
    'bg-gray-100',
    'text-cyan-600',
    'hover:bg-gray-100',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

