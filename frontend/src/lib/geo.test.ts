import { describe, expect, it } from "vitest";
import { bbox, imageCoords } from "@/lib/geo";

describe("geo", () => {
  it("computes bbox from a ring", () => {
    expect(
      bbox([
        [
          [0, 0],
          [2, 0],
          [2, 3],
          [0, 3],
          [0, 0],
        ],
      ]),
    ).toEqual([0, 0, 2, 3]);
  });
  it("orders image corners TL,TR,BR,BL", () => {
    expect(imageCoords([0, 0, 2, 3])).toEqual([
      [0, 3],
      [2, 3],
      [2, 0],
      [0, 0],
    ]);
  });
});
