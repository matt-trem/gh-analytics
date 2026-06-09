#!/usr/bin/env node
// GitHub contribution stats — daily / weekly / monthly / yearly

import { readFileSync } from "fs";
import { resolve } from "path";

// Load .env from the script's directory
try {
  const lines = readFileSync(resolve(import.meta.dirname, ".env"), "utf8").split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    const val = trimmed.slice(eq + 1).trim().replace(/^["']|["']$/g, "");
    if (key && !(key in process.env)) process.env[key] = val;
  }
} catch {}

const GITHUB_GRAPHQL = "https://api.github.com/graphql";

const CONTRIBUTIONS_QUERY = `
query($from: DateTime!, $to: DateTime!) {
  viewer {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}`;

interface ContributionDay {
  date: string;
  contributionCount: number;
}

interface GraphQLResponse {
  data?: {
    viewer: {
      contributionsCollection: {
        contributionCalendar: {
          weeks: Array<{ contributionDays: ContributionDay[] }>;
        };
      };
    };
  };
  errors?: Array<{ message: string }>;
}

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

async function fetchYear(
  token: string,
  year: number
): Promise<Map<string, number>> {
  const resp = await fetch(GITHUB_GRAPHQL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: CONTRIBUTIONS_QUERY,
      variables: {
        from: `${year}-01-01T00:00:00Z`,
        to: `${year}-12-31T23:59:59Z`,
      },
    }),
  });

  if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);

  const payload = (await resp.json()) as GraphQLResponse;
  if (payload.errors) {
    for (const e of payload.errors) console.error(`GraphQL error: ${e.message}`);
    process.exit(1);
  }

  const counts = new Map<string, number>();
  const weeks = payload.data!.viewer.contributionsCollection.contributionCalendar.weeks;
  for (const week of weeks) {
    for (const day of week.contributionDays) {
      counts.set(day.date, day.contributionCount);
    }
  }
  return counts;
}

async function fetchAll(
  token: string,
  sinceYear: number
): Promise<Map<string, number>> {
  const today = new Date();
  const all = new Map<string, number>();
  for (let year = sinceYear; year <= today.getFullYear(); year++) {
    console.error(`  Fetching ${year}...`);
    const yearly = await fetchYear(token, year);
    for (const [date, count] of yearly) all.set(date, count);
  }
  return all;
}

function printDaily(counts: Map<string, number>, days = 30): void {
  console.log(`\n${"DATE".padEnd(12)} ${"COUNT".padStart(5)}  CHART`);
  console.log("-".repeat(50));
  const today = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = isoDate(d);
    const c = counts.get(key) ?? 0;
    const bar = "#".repeat(Math.min(c, 40));
    console.log(`${key.padEnd(12)} ${String(c).padStart(5)}  ${bar}`);
  }
}

function printWeekly(counts: Map<string, number>, weeks = 12): void {
  console.log(`\n${"WEEK START".padEnd(12)} ${"COUNT".padStart(5)}`);
  console.log("-".repeat(18));
  const today = new Date();
  const dayOfWeek = today.getDay(); // 0 = Sunday
  const weekStart = new Date(today);
  weekStart.setDate(today.getDate() - ((dayOfWeek + 6) % 7)); // Monday-based
  for (let i = weeks - 1; i >= 0; i--) {
    const ws = new Date(weekStart);
    ws.setDate(weekStart.getDate() - i * 7);
    let total = 0;
    for (let d = 0; d < 7; d++) {
      const day = new Date(ws);
      day.setDate(ws.getDate() + d);
      total += counts.get(isoDate(day)) ?? 0;
    }
    console.log(`${isoDate(ws).padEnd(12)} ${String(total).padStart(5)}`);
  }
}

function printMonthly(counts: Map<string, number>, months = 12): void {
  console.log(`\n${"MONTH".padEnd(10)} ${"COUNT".padStart(5)}`);
  console.log("-".repeat(16));
  const today = new Date();
  let year = today.getFullYear();
  let month = today.getMonth() + 1;
  const results: Array<[string, number]> = [];
  for (let i = 0; i < months; i++) {
    const label = `${year}-${String(month).padStart(2, "0")}`;
    let total = 0;
    for (const [date, count] of counts) {
      if (date.startsWith(label)) total += count;
    }
    results.push([label, total]);
    month--;
    if (month === 0) { month = 12; year--; }
  }
  for (const [label, total] of results.reverse()) {
    console.log(`${label.padEnd(10)} ${String(total).padStart(5)}`);
  }
}

function printYearly(counts: Map<string, number>): void {
  console.log(`\n${"YEAR".padEnd(6)} ${"COUNT".padStart(5)}`);
  console.log("-".repeat(12));
  const byYear = new Map<number, number>();
  for (const [date, count] of counts) {
    const y = parseInt(date.slice(0, 4));
    byYear.set(y, (byYear.get(y) ?? 0) + count);
  }
  for (const year of [...byYear.keys()].sort()) {
    console.log(`${String(year).padEnd(6)} ${String(byYear.get(year)).padStart(5)}`);
  }
}

async function main(): Promise<void> {
  const token = process.env["GITHUB_TOKEN"];
  if (!token) {
    console.error("Error: set GITHUB_TOKEN in .env or environment.");
    process.exit(1);
  }

  const username = process.env["GITHUB_USER"] ?? "matt-trem";
  const sinceYear = parseInt(process.env["GITHUB_SINCE_YEAR"] ?? String(new Date().getFullYear() - 2));

  console.error(`Fetching GitHub contributions for @${username} (since ${sinceYear})...`);
  const counts = await fetchAll(token, sinceYear);

  const total = [...counts.values()].reduce((a, b) => a + b, 0);
  console.error(`  ${total} total contributions across ${counts.size} days.`);

  console.log("\n=== DAILY (last 30 days) ===");
  printDaily(counts);

  console.log("\n=== WEEKLY (last 12 weeks) ===");
  printWeekly(counts);

  console.log("\n=== MONTHLY (last 12 months) ===");
  printMonthly(counts);

  console.log("\n=== YEARLY ===");
  printYearly(counts);
}

main().catch((e) => {
  console.error((e as Error).message);
  process.exit(1);
});
