# TerraLedger MRV Platform

A polished front-end demonstration of an agricultural carbon-credit MRV marketplace. It includes distinct Farm Operator, Verifier, Researcher, and Investor workspaces, backed by a shared in-memory mock service layer.

## Run locally

```bash
npm install
npm run dev
```

Open the Vite address shown in the terminal. Use the role selector or any of these demo accounts; the password can be any four or more characters:

- `ava@terraledger.demo` — Farm Operator
- `lina@terraledger.demo` — Verifier
- `sam@terraledger.demo` — Researcher
- `noah@terraledger.demo` — Investor

## Demo flow

Register a farm as Ava, approve it as Lina, then find the newly created project in the Investor marketplace. Data persists during the browser session and resets on a full reload.
