// Разбор файла <имя>_timeElapsed.csv (датасет Gomez et al. 2022)
// и сопоставление времени с кадрами F0.

export class TimeElapsedError extends Error {}

export type TimeElapsedResult = {
  /** Время (ч) для каждого оставленного кадра, в порядке кадров. */
  hours: number[];
  /** Индексы оставленных кадров в исходном списке. */
  keepIndices: number[];
  /** Кадры без времени в файле (удалены). */
  droppedFrames: number;
  /** Значения времени без соответствующего кадра (отброшены). */
  droppedTimes: number;
  matchedBy: "frame" | "order";
};

const toNumber = (cell: string): number => {
  const value = cell.trim().replace(/^"|"$/g, "").replace(",", ".");
  return value === "" ? NaN : Number(value);
};

/** Номер кадра из имени файла: RUN123 → 123, иначе последнее число в имени. */
export function frameNumberFromName(name: string): number | null {
  const base = name.replace(/\.[^.]+$/, "");
  const run = base.match(/RUN(\d+)/i);
  if (run) return Number(run[1]);
  const numbers = base.match(/\d+/g);
  return numbers ? Number(numbers[numbers.length - 1]) : null;
}

export function parseTimeElapsed(
  text: string,
  frameNames: string[],
): TimeElapsedResult {
  const lines = text
    .replace(/^﻿/, "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (!lines.length) throw new TimeElapsedError("Не удалось прочитать файл");

  const first = lines[0];
  const delimiter =
    (first.match(/;/g)?.length ?? 0) > (first.match(/,/g)?.length ?? 0)
      ? ";"
      : ",";
  let rows = lines.map((line) => line.split(delimiter).map((c) => c.trim()));

  // Заголовок — первая строка, в которой нет ни одного числа.
  const hasHeader = !rows[0].some((cell) => Number.isFinite(toNumber(cell)));
  const header = hasHeader
    ? rows[0].map((cell) => cell.replace(/^"|"$/g, "").toLowerCase())
    : [];
  if (hasHeader) rows = rows.slice(1);
  if (!rows.length) throw new TimeElapsedError("В файле нет колонки со временем");

  const columns = Math.max(...rows.map((row) => row.length), header.length);
  const isNumericColumn = (index: number) =>
    rows.every((row) => Number.isFinite(toNumber(row[index] ?? "")));

  let timeColumn = header.findIndex((name) => name.includes("time"));
  if (timeColumn < 0) {
    for (let index = columns - 1; index >= 0; index--)
      if (isNumericColumn(index)) {
        timeColumn = index;
        break;
      }
  }
  if (timeColumn < 0) throw new TimeElapsedError("В файле нет колонки со временем");

  const frameColumn = header.findIndex(
    (name, index) =>
      index !== timeColumn && (name.includes("frame") || name.includes("index")),
  );

  // Строки с нечисловым временем не используются.
  const entries = rows
    .map((row) => ({
      time: toNumber(row[timeColumn] ?? ""),
      frame: frameColumn >= 0 ? toNumber(row[frameColumn] ?? "") : NaN,
    }))
    .filter((entry) => Number.isFinite(entry.time));
  if (!entries.length) throw new TimeElapsedError("В файле нет колонки со временем");

  // Кадры ещё не загружены: просто возвращаем все значения.
  if (!frameNames.length)
    return {
      hours: entries.map((entry) => entry.time),
      keepIndices: [],
      droppedFrames: 0,
      droppedTimes: 0,
      matchedBy: frameColumn >= 0 ? "frame" : "order",
    };

  if (frameColumn < 0) {
    if (entries.length !== frameNames.length)
      throw new TimeElapsedError(
        `Кадров: ${frameNames.length}, значений времени: ${entries.length}`,
      );
    return {
      hours: entries.map((entry) => entry.time),
      keepIndices: frameNames.map((_, index) => index),
      droppedFrames: 0,
      droppedTimes: 0,
      matchedBy: "order",
    };
  }

  const byFrame = new Map<number, number>();
  for (const entry of entries)
    if (Number.isFinite(entry.frame) && !byFrame.has(entry.frame))
      byFrame.set(entry.frame, entry.time);

  const hours: number[] = [];
  const keepIndices: number[] = [];
  const used = new Set<number>();
  frameNames.forEach((name, index) => {
    const number = frameNumberFromName(name);
    if (number === null || !byFrame.has(number) || used.has(number)) return;
    used.add(number);
    hours.push(byFrame.get(number)!);
    keepIndices.push(index);
  });
  if (!hours.length)
    throw new TimeElapsedError(
      `Кадров: ${frameNames.length}, значений времени: ${entries.length}. Номера кадров в именах файлов не совпали с номерами в файле.`,
    );
  return {
    hours,
    keepIndices,
    droppedFrames: frameNames.length - keepIndices.length,
    droppedTimes: entries.length - keepIndices.length,
    matchedBy: "frame",
  };
}
