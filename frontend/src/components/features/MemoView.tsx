"use client";
import { useMemo } from "react";
import { Table, Thead, Th, Tbody, Td } from "@/components/ui/Table";

/** Renders generated memo text as a readable prose document.
 * Memo content is lightly-formatted markdown (headings, bullets, bold, pipe tables) — this
 * is a small dependency-free parser rather than a full markdown renderer. */

type Block =
  | { type: "heading"; level: 1 | 2 | 3 | 4; text: string }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "table"; headers: string[]; rows: string[][] }
  | { type: "paragraph"; text: string };

/** Split a `|`-delimited table row into trimmed cells, dropping the empty
 * leading/trailing cell produced by the row's outer pipes. */
function splitTableRow(line: string): string[] {
  let inner = line.trim();
  if (inner.startsWith("|")) inner = inner.slice(1);
  if (inner.endsWith("|")) inner = inner.slice(0, -1);
  return inner.split("|").map((cell) => cell.trim());
}

/** A separator row like `|---|:--:|` — cells containing only `-`, `:`, and spaces. */
function isTableSeparatorRow(line: string): boolean {
  if (!line.startsWith("|")) return false;
  const cells = splitTableRow(line);
  return cells.length > 0 && cells.every((cell) => /^:?-+:?$/.test(cell));
}

function parseBlocks(content: string): Block[] {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let paragraph: string[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;

  const flushParagraph = () => {
    if (paragraph.length) {
      blocks.push({ type: "paragraph", text: paragraph.join(" ").trim() });
      paragraph = [];
    }
  };
  const flushList = () => {
    if (list && list.items.length) blocks.push({ type: "list", ordered: list.ordered, items: list.items });
    list = null;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) {
      flushParagraph();
      flushList();
      continue;
    }

    if (line.startsWith("|") && i + 1 < lines.length && isTableSeparatorRow(lines[i + 1].trim())) {
      flushParagraph();
      flushList();
      const headers = splitTableRow(line);
      const rows: string[][] = [];
      i += 2; // skip the header row and the separator row
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        rows.push(splitTableRow(lines[i].trim()));
        i++;
      }
      i--; // compensate for the for-loop's increment
      blocks.push({ type: "table", headers, rows });
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      flushParagraph();
      flushList();
      const level = Math.min(heading[1].length, 4) as 1 | 2 | 3 | 4;
      blocks.push({ type: "heading", level, text: heading[2] });
      continue;
    }
    const bullet = line.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      flushParagraph();
      if (!list || list.ordered) {
        flushList();
        list = { ordered: false, items: [] };
      }
      list.items.push(bullet[1]);
      continue;
    }
    const numbered = line.match(/^\d+\.\s+(.*)$/);
    if (numbered) {
      flushParagraph();
      if (!list || !list.ordered) {
        flushList();
        list = { ordered: true, items: [] };
      }
      list.items.push(numbered[1]);
      continue;
    }
    flushList();
    paragraph.push(line);
  }
  flushParagraph();
  flushList();
  return blocks;
}

/** Render `**bold**` spans within inline text; everything else passes through. */
function renderInline(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i} className="font-semibold text-ink">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <span key={i}>{part}</span>
    ),
  );
}

export function MemoView({ content }: { content: string }) {
  const blocks = useMemo(() => parseBlocks(content), [content]);

  if (blocks.length === 0) {
    return <p className="text-sm text-muted">No content.</p>;
  }

  return (
    <div className="max-w-none space-y-4 text-[15px] leading-relaxed text-ink">
      {blocks.map((block, i) => {
        if (block.type === "heading") {
          if (block.level === 1)
            return (
              <h2 key={i} className="pt-2 text-xl font-semibold text-ink first:pt-0">
                {renderInline(block.text)}
              </h2>
            );
          if (block.level === 2)
            return (
              <h3 key={i} className="pt-2 text-lg font-semibold text-ink first:pt-0">
                {renderInline(block.text)}
              </h3>
            );
          if (block.level === 3)
            return (
              <h4 key={i} className="pt-1 text-base font-semibold text-ink">
                {renderInline(block.text)}
              </h4>
            );
          return (
            <h5 key={i} className="label pt-1">
              {block.text}
            </h5>
          );
        }
        if (block.type === "table") {
          return (
            <Table key={i}>
              <Thead>
                <tr>
                  {block.headers.map((header, j) => (
                    <Th key={j}>{renderInline(header)}</Th>
                  ))}
                </tr>
              </Thead>
              <Tbody>
                {block.rows.map((row, ri) => (
                  <tr key={ri} className="border-b border-border last:border-0">
                    {row.map((cell, ci) => (
                      <Td key={ci}>{renderInline(cell)}</Td>
                    ))}
                  </tr>
                ))}
              </Tbody>
            </Table>
          );
        }
        if (block.type === "list") {
          const items = (
            <>
              {block.items.map((item, j) => (
                <li key={j} className="leading-relaxed text-ink">
                  {renderInline(item)}
                </li>
              ))}
            </>
          );
          return block.ordered ? (
            <ol key={i} className="list-decimal space-y-1 pl-5">
              {items}
            </ol>
          ) : (
            <ul key={i} className="list-disc space-y-1 pl-5">
              {items}
            </ul>
          );
        }
        return (
          <p key={i} className="leading-relaxed text-ink">
            {renderInline(block.text)}
          </p>
        );
      })}
    </div>
  );
}
