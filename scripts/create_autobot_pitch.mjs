import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "/Users/kossybayevalan/Documents/Codex/2026-06-22/ha89ter-netizen-v2-https-github-com/work/repo/outputs/autobot_ai_automotive_care_pitch_en.pptx";
const PREVIEW_DIR = "/private/tmp/codex-presentations/autobot-pitch/tmp/preview";
const LAYOUT_DIR = "/private/tmp/codex-presentations/autobot-pitch/tmp/layout";

const W = 1280;
const H = 720;
const M = 54;
const INK = "#0A0A0A";
const MUTED = "#565656";
const PANEL = "#EDEDED";
const RULE = "#B8BCC4";
const ACCENT = "#FF6B35";
const WHITE = "#FFFFFF";

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

function addText(slide, text, x, y, w, h, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: opts.size ?? 22,
    color: opts.color ?? INK,
    bold: opts.bold ?? false,
    alignment: opts.align ?? "left",
    fontFace: "Helvetica Neue",
  };
  return shape;
}

function panel(slide, x, y, w, h, fill = PANEL, line = "none") {
  return slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
  });
}

function accentBar(slide, x, y, h) {
  panel(slide, x, y, 8, h, ACCENT);
}

function footer(slide, n) {
  addText(slide, "AutoBot / AI Automotive Care Platform", M, 666, 520, 24, {
    size: 14,
    color: MUTED,
    bold: true,
  });
  addText(slide, String(n).padStart(2, "0"), 1172, 666, 54, 24, {
    size: 14,
    color: MUTED,
    bold: true,
    align: "right",
  });
}

function slideTitle(slide, title, kicker, n) {
  if (kicker) addText(slide, kicker.toUpperCase(), M, 42, 420, 24, { size: 14, color: MUTED, bold: true });
  addText(slide, title, M, 78, 820, 72, { size: 40, bold: true });
  panel(slide, M, 162, 1170, 1, RULE);
  footer(slide, n);
}

function bulletList(slide, items, x, y, w, size = 22, gap = 52) {
  items.forEach((item, i) => {
    const yy = y + i * gap;
    panel(slide, x, yy + 8, 9, 9, ACCENT);
    addText(slide, item, x + 28, yy, w - 28, gap - 4, { size, color: INK });
  });
}

function metric(slide, value, label, x, y, w, h = 128) {
  panel(slide, x, y, w, h, PANEL);
  addText(slide, value, x + 24, y + 24, w - 48, 48, { size: 38, bold: true });
  addText(slide, label, x + 24, y + 82, w - 48, 38, { size: 18, color: MUTED });
}

function stage(slide, label, x, y, w, index) {
  panel(slide, x, y, w, 104, PANEL);
  addText(slide, String(index), x + 18, y + 18, 38, 34, { size: 26, bold: true, color: ACCENT });
  addText(slide, label, x + 66, y + 20, w - 84, 62, { size: 21, bold: true });
}

function addCover(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  panel(slide, 0, 0, W, H, WHITE);
  panel(slide, 744, 0, 536, 720, PANEL);
  panel(slide, 790, 66, 398, 242, WHITE, RULE);
  panel(slide, 790, 338, 398, 250, WHITE, RULE);
  accentBar(slide, M, 96, 94);
  addText(slide, "AutoBot", M + 28, 86, 540, 70, { size: 64, bold: true });
  addText(slide, "AI Automotive Care Platform", M + 30, 162, 540, 42, { size: 24, color: MUTED });
  addText(slide, "From a driver's symptom to diagnosis, parts, repair guidance, and the right local service inside Telegram.", M, 304, 600, 126, { size: 30 });
  addText(slide, "Investor / partner pitch deck", M, 612, 420, 30, { size: 17, color: MUTED, bold: true });
  addText(slide, "MVP built\nProduct logic tested\nReady for pilots", 824, 126, 300, 120, { size: 30, bold: true });
  addText(slide, "Designed to become a vehicle-care operating layer: diagnostics, safety, parts, services, reminders, and data.", 824, 396, 300, 110, { size: 23, color: MUTED });
  footer(slide, 1);
}

function addProblem(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  slideTitle(slide, "Car ownership is fragmented at the worst moment", "Problem", 2);
  bulletList(slide, [
    "Drivers cannot reliably translate symptoms into the right next action.",
    "Generic AI answers can miss safety risk or ignore the exact vehicle.",
    "Service discovery is noisy: repair shop, dealer, tow, tire shop, parts store are different needs.",
    "Parts buying is confusing: OEM, trusted analog, cheap analog, VIN fitment, and budget tradeoffs.",
  ], M, 210, 650, 23, 76);
  panel(slide, 812, 214, 360, 314, PANEL);
  addText(slide, "Moment of truth", 846, 248, 290, 34, { size: 26, bold: true });
  addText(slide, "When a car breaks, the user needs a safe path, not a search result.", 846, 310, 276, 96, { size: 26 });
  addText(slide, "AutoBot owns that path.", 846, 452, 276, 48, { size: 27, bold: true, color: ACCENT });
}

function addSolution(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  slideTitle(slide, "One assistant guides the full repair journey", "Solution", 3);
  const y = 238;
  const xs = [58, 282, 506, 730, 954];
  const labels = ["Problem", "Diagnosis", "Part match", "DIY or service", "History"];
  labels.forEach((label, i) => stage(slide, label, xs[i], y, 170, i + 1));
  for (let i = 0; i < 4; i++) panel(slide, xs[i] + 176, y + 52, 44, 2, INK);
  addText(slide, "The core difference: AutoBot does not stop at advice. It moves the user toward a safe decision and a concrete outcome.", M, 440, 760, 92, { size: 29, bold: true });
  panel(slide, 882, 442, 300, 92, PANEL);
  addText(slide, "Telegram-first", 906, 466, 244, 28, { size: 24, bold: true });
  addText(slide, "No app install required for MVP pilots.", 906, 502, 244, 26, { size: 18, color: MUTED });
}

function addProduct(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  slideTitle(slide, "What the MVP already does", "Product", 4);
  const cards = [
    ["AI diagnostics", "Vehicle-aware advice with VIN / garage context."],
    ["Safety triage", "Blocks unsafe DIY for brakes, steering, fire, fuel leaks, overheating."],
    ["Parts intelligence", "OEM original, quality aftermarket, budget aftermarket, search links."],
    ["Service routing", "Dealer center, repair shop, tow, tire shop, diagnostics, parts store."],
    ["Photo analysis", "Dashboard, tire, leak, body damage, under-hood part context."],
    ["Retention layer", "Garage, history, reminders, reset, admin stats, bilingual UX."],
  ];
  cards.forEach(([h, b], i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = M + col * 394;
    const y = 205 + row * 190;
    panel(slide, x, y, 350, 144, PANEL);
    panel(slide, x + 22, y + 24, 10, 10, ACCENT);
    addText(slide, h, x + 46, y + 18, 276, 32, { size: 24, bold: true });
    addText(slide, b, x + 46, y + 62, 268, 58, { size: 18, color: MUTED });
  });
}

function addDifferentiation(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  slideTitle(slide, "Why this is more than another chatbot", "Differentiation", 5);
  metric(slide, "Context", "VIN, garage, selected vehicle, location, history", M, 206, 258);
  metric(slide, "Safety", "Risk-aware flows before DIY advice", 344, 206, 258);
  metric(slide, "Action", "Parts, services, routes, repair guidance", 634, 206, 258);
  metric(slide, "Market", "Built to plug into suppliers, dealers, fleets", 924, 206, 258);
  addText(slide, "The winning wedge is not AI answer generation. It is guided automotive decision-making with local execution.", M, 432, 820, 84, { size: 31, bold: true });
  addText(slide, "This creates future monetization points across referrals, parts, booking, fleets, dealer networks, and insurance.", M, 544, 920, 46, { size: 21, color: MUTED });
}

function addTech(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  slideTitle(slide, "Strong MVP codebase built for expansion", "Technical foundation", 6);
  bulletList(slide, [
    "Python + Aiogram 3 FSM flows for diagnosis, garage, location, photo, parts, reminders.",
    "Service layer around OpenAI, Google Places, VIN decoding, safety, parts, and response quality.",
    "SQLite persistence with local FSM storage, cached answers, feedback, API usage, and admin stats.",
    "Parts module uses mock provider now, but is shaped for TecDoc, PartSouq, Emex, Autodoc, Kaspi.",
    "51 automated tests pass across parts, places, reminders, i18n, safety, and critical user logic.",
  ], M, 204, 740, 20, 66);
  panel(slide, 886, 220, 296, 272, PANEL);
  addText(slide, "Engineering thesis", 916, 248, 240, 30, { size: 24, bold: true });
  addText(slide, "Keep the Telegram MVP lean, but design every integration behind service boundaries so funding can upgrade data providers without rewriting the bot.", 916, 308, 226, 128, { size: 20, color: MUTED });
}

function addBusiness(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  slideTitle(slide, "Business model expands with integrations", "Commercial path", 7);
  const rows = [
    ["Now", "Telegram MVP", "User testing, demos, partner pilots"],
    ["Phase 1", "Service referrals", "Lead generation for repair shops, dealers, tow providers"],
    ["Phase 2", "Parts marketplace", "Affiliate / commission from fitment-aware part recommendations"],
    ["Phase 3", "B2B platform", "Fleets, dealers, insurance, maintenance workflows"],
  ];
  rows.forEach((r, i) => {
    const y = 200 + i * 92;
    panel(slide, M, y, 110, 62, i === 0 ? ACCENT : PANEL);
    addText(slide, r[0], M + 18, y + 18, 78, 24, { size: 18, bold: true, color: i === 0 ? WHITE : INK });
    addText(slide, r[1], 204, y + 12, 310, 32, { size: 25, bold: true });
    addText(slide, r[2], 540, y + 14, 600, 42, { size: 20, color: MUTED });
    panel(slide, M, y + 78, 1110, 1, RULE);
  });
}

function addRoadmap(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  slideTitle(slide, "Funding turns the MVP into infrastructure", "Roadmap", 8);
  const tracks = [
    ["Data", "TecDoc, PartSouq, VIN fitment, real inventory, pricing"],
    ["Transactions", "Booking, payments, service CRM, parts checkout"],
    ["Distribution", "Dealer network, fleet dashboard, insurance partnerships"],
    ["Product", "Mobile app, voice/photo-first flows, predictive reminders"],
  ];
  tracks.forEach(([h, b], i) => {
    const x = M + i * 292;
    panel(slide, x, 220, 246, 294, PANEL);
    addText(slide, `0${i + 1}`, x + 24, 246, 56, 32, { size: 26, bold: true, color: ACCENT });
    addText(slide, h, x + 24, 304, 190, 34, { size: 27, bold: true });
    addText(slide, b, x + 24, 372, 190, 94, { size: 19, color: MUTED });
  });
  addText(slide, "The product should grow by replacing mocks with paid integrations, not by rebuilding the customer journey.", M, 562, 920, 38, { size: 22, bold: true });
}

function addValidation(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  slideTitle(slide, "Current validation assets", "Proof points", 9);
  metric(slide, "154", "automated tests passed", M, 210, 210, 144);
  metric(slide, "100", "supported vehicles covered by automated tests", 304, 210, 270, 144);
  metric(slide, "2", "languages in core user flows", 626, 210, 270, 144);
  metric(slide, "17", "service categories", 948, 210, 230, 144);
  bulletList(slide, [
    "Admin commands and API usage stats are already present for operator control.",
    "Local common answers and cache reduce AI spend during repeated issues.",
    "Mock parts intelligence creates a full demo without paid supplier APIs.",
    "Google Places integration supports local search with category and radius controls.",
  ], M, 440, 920, 20, 48);
}

function addAsk(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  panel(slide, 0, 0, W, H, WHITE);
  panel(slide, M, 74, 1172, 470, PANEL);
  accentBar(slide, 106, 138, 84);
  addText(slide, "What we need next", 136, 128, 660, 66, { size: 54, bold: true });
  addText(slide, "Pilot users, service partners, and funding for real automotive data integrations.", 136, 234, 760, 78, { size: 30 });
  addText(slide, "Immediate next steps", 136, 384, 270, 34, { size: 24, bold: true });
  addText(slide, "1. Run QA pilots with real drivers\n2. Connect real parts/service data\n3. Measure conversion from symptom to action\n4. Package B2B pilots for dealers and fleets", 136, 430, 720, 110, { size: 22, color: MUTED });
  addText(slide, "AutoBot can become the guided care layer between drivers, parts, and services.", 742, 612, 430, 42, { size: 22, bold: true, align: "right" });
  footer(slide, 10);
}

async function main() {
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(LAYOUT_DIR, { recursive: true });
  await fs.mkdir(new URL(".", `file://${OUT}`).pathname, { recursive: true });

  const presentation = Presentation.create({ slideSize: { width: W, height: H } });
  addCover(presentation);
  addProblem(presentation);
  addSolution(presentation);
  addProduct(presentation);
  addDifferentiation(presentation);
  addTech(presentation);
  addBusiness(presentation);
  addRoadmap(presentation);
  addValidation(presentation);
  addAsk(presentation);

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(`${PREVIEW_DIR}/${stem}.png`, await presentation.export({ slide, format: "png", scale: 1 }));
    await fs.writeFile(`${LAYOUT_DIR}/${stem}.layout.json`, await (await slide.export({ format: "layout" })).text());
  }
  await writeBlob(`${PREVIEW_DIR}/deck-montage.webp`, await presentation.export({ format: "webp", montage: true, scale: 1 }));
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(OUT);
  console.log(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
