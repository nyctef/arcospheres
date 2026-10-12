import type { BufferGeometry, LineSegments, Material } from "three";

export type Position4D = readonly [x: number, y: number, z: number, w: number];

export type Edge4D = readonly [start: number, end: number];

export interface Object4DGeometry {
  readonly vertices: readonly Position4D[];
  readonly edges: readonly Edge4D[];
}

export interface Wireframe4D extends Object4DGeometry {
  readonly object3d: LineSegments<BufferGeometry, Material | Material[]>;
  updateProjection(): void;
}