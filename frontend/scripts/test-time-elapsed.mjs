// Checks parseTimeElapsed without a test runner: transpile the TS source and assert.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { transformWithOxc } from "vite";

await fs.mkdir(path.resolve("node_modules/.tmp"), { recursive: true });
const directory = await fs.mkdtemp(path.resolve("node_modules/.tmp/time-check-"));
try {
  const source = await fs.readFile("src/utils/parseTimeElapsed.ts", "utf8");
  const file = path.join(directory, "parseTimeElapsed.mjs");
  await fs.writeFile(file, (await transformWithOxc(source, "parseTimeElapsed.ts")).code);
  const { parseTimeElapsed, frameNumberFromName, TimeElapsedError } = await import(
    pathToFileURL(file).href
  );
  const names = ["E1_RUN1.jpeg", "E1_RUN2.jpeg", "E1_RUN3.jpeg"];

  assert.equal(frameNumberFromName("D2013_S0675_I141_1_RUN123.jpeg"), 123);
  assert.equal(frameNumberFromName("frame_12_045.png"), 45);
  assert.equal(frameNumberFromName("frame.png"), null);

  // Header with frame column, comma delimiter: match by number.
  let r = parseTimeElapsed("frame_index,time\n1,0.0\n2,0.25\n3,0.5\n", names);
  assert.deepEqual(r.hours, [0, 0.25, 0.5]);
  assert.equal(r.matchedBy, "frame");
  assert.equal(r.droppedFrames, 0);

  // Semicolon delimiter, decimal comma, extra time and missing frame.
  r = parseTimeElapsed("Frame;Time\n1;0\n3;0,5\n4;0,75\n", names);
  assert.deepEqual(r.hours, [0, 0.5]);
  assert.deepEqual(r.keepIndices, [0, 2]);
  assert.equal(r.droppedFrames, 1);
  assert.equal(r.droppedTimes, 1);

  // No header, no frame column: last numeric column, by order.
  r = parseTimeElapsed("a,0\nb,1\nc,2", names);
  assert.deepEqual(r.hours, [0, 1, 2]);
  assert.equal(r.matchedBy, "order");

  // Order mode with count mismatch.
  assert.throws(
    () => parseTimeElapsed("time\n0\n1", names),
    (e) => e instanceof TimeElapsedError && e.message === "Кадров: 3, значений времени: 2",
  );
  // No time column.
  assert.throws(
    () => parseTimeElapsed("name,comment\na,b", names),
    (e) => e.message === "В файле нет колонки со временем",
  );
  assert.throws(() => parseTimeElapsed("", names), /Не удалось прочитать файл/);

  console.log("parseTimeElapsed: all checks passed");
} finally {
  await fs.rm(directory, { recursive: true, force: true });
}
