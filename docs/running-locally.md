# Running locally

## Prerequisites

Install Node.js and npm.

A recent LTS version of Node.js is recommended.

## Install dependencies

From the repository root:

```bash
npm install
```

## Run the development server

```bash
npm run dev
```

The Vite dev server is configured in `package.json` to run on port `3000` and bind to `0.0.0.0`.

Open the local URL shown in the terminal.

## Build

```bash
npm run build
```

## Preview production build

```bash
npm run preview
```

## TypeScript check

```bash
npm run lint
```

This currently runs:

```bash
tsc --noEmit
```

## Environment variables

The original AI Studio export may mention `.env.local` and `GEMINI_API_KEY`. The current simulation should not depend on Gemini at runtime unless future features explicitly add AI calls.

If the app runs without AI features, missing Gemini credentials should not prevent the core simulation from working.

## Troubleshooting

If dependencies fail to install, delete `node_modules` and reinstall:

```bash
rm -rf node_modules
npm install
```

On Windows PowerShell:

```powershell
Remove-Item -Recurse -Force node_modules
npm install
```

If port 3000 is already in use, stop the other process or change the port in `package.json`.

If the canvas is blank, check the browser console and run the TypeScript check.