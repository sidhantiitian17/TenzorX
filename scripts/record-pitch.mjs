import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const APP_URL = "https://tenzor-x.vercel.app";
const OUTPUT_DIR = path.resolve("pitch-videos");

const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function clickIfVisible(page, name) {
  const target = page.getByRole("button", { name, exact: false }).first();
  if (await target.isVisible().catch(() => false)) {
    await target.click();
    await pause(600);
    return true;
  }
  return false;
}

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({
    headless: false,
    args: ["--start-maximized"],
  });

  const context = await browser.newContext({
    viewport: { width: 1366, height: 768 },
    recordVideo: {
      dir: OUTPUT_DIR,
      size: { width: 1280, height: 720 },
    },
  });

  const page = await context.newPage();

  await page.goto(APP_URL, { waitUntil: "domcontentloaded" });
  await pause(1200);

  await clickIfVisible(page, "Minimize disclaimer");

  // Open profile and set context for an investor-worthy demo.
  await clickIfVisible(page, "Add Location & Budget");
  await page.getByPlaceholder("Enter your city").fill("Raipur");
  await pause(400);
  await clickIfVisible(page, "Diabetes");
  await clickIfVisible(page, "Apply & Search");
  await clickIfVisible(page, "Close");

  // Trigger a realistic query.
  await clickIfVisible(page, "Best cancer hospital in Raipur");
  await page.getByRole("button", { name: /View Results/i }).waitFor({ timeout: 30000 });
  await pause(500);
  await clickIfVisible(page, "View Results");

  // Highlight confidence, cost intelligence, and detail depth.
  await clickIfVisible(page, "View Cost Breakdown");
  await clickIfVisible(page, "View Details");
  await clickIfVisible(page, "Compare");
  await pause(1500);

  // Show product controls from sidebar.
  await clickIfVisible(page, "Close");
  await page.getByRole("banner").getByRole("button").first().click();
  await pause(600);
  await clickIfVisible(page, "Lender / Insurer Mode");
  await clickIfVisible(page, "Dark Mode");
  await pause(1200);

  const video = page.video();
  await context.close();
  await browser.close();

  const rawVideoPath = await video.path();
  const targetPath = path.join(
    OUTPUT_DIR,
    `tenzorx-investor-pitch-${new Date().toISOString().replace(/[:.]/g, "-")}.webm`
  );

  fs.copyFileSync(rawVideoPath, targetPath);

  console.log("Pitch video saved:");
  console.log(targetPath);
}

main().catch((error) => {
  console.error("Pitch recording failed:", error);
  process.exitCode = 1;
});
