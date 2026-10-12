import type { BufferGeometry, LineSegments, Material, Vector4 } from "three";

export type Edge4D = readonly [start: number, end: number];

export interface Object4DGeometry {
  readonly vertices: readonly Vector4[];
  readonly edges: readonly Edge4D[];
}

export interface Wireframe4D extends Object4DGeometry {
  readonly object3d: LineSegments<BufferGeometry, Material | Material[]>;
  updateProjection(): void;
}