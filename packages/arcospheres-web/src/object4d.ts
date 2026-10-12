import * as THREE from "three";
import { project4to3 } from "./coords4d";
import type { Edge4D, Wireframe4D } from "./types";

/** A wireframe 4D object: 4D vertices plus edges (pairs of vertex indices). */
export class Object4D implements Wireframe4D {
  readonly vertices: readonly THREE.Vector4[];
  readonly edges: readonly Edge4D[];
  readonly object3d: THREE.LineSegments<THREE.BufferGeometry, THREE.Material | THREE.Material[]>;

  constructor(
    vertices: readonly THREE.Vector4[],
    edges: readonly Edge4D[],
    material: THREE.Material | THREE.Material[],
  ) {
    this.vertices = vertices;
    this.edges = edges;
    const positions = new Float32Array(edges.length * 2 * 3);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    this.object3d = new THREE.LineSegments(geometry, material);
    this.object3d.frustumCulled = false;
    this.updateProjection();
  }

  /** Recompute the 3D line positions from the 4D vertices. */
  updateProjection(): void {
    const attribute = this.object3d.geometry.getAttribute("position");
    const projected = new THREE.Vector3();
    let attributeIndex = 0;
    for (const edge of this.edges) {
      for (const vertexIndex of edge) {
        const vertex = this.vertices[vertexIndex];
        if (vertex === undefined) {
          throw new RangeError(`Edge references missing vertex ${vertexIndex}`);
        }
        project4to3(vertex, undefined, undefined, projected);
        attribute.setXYZ(attributeIndex++, projected.x, projected.y, projected.z);
      }
    }
    attribute.needsUpdate = true;
  }
}

/** Unit tesseract with vertices at every combination of 0/1 in x,y,z,w. */
export function createTesseract(material: THREE.Material | THREE.Material[]): Object4D {
  const vertices: THREE.Vector4[] = [];
  for (let vertexIndex = 0; vertexIndex < 16; vertexIndex++) {
    vertices.push(new THREE.Vector4(
      vertexIndex & 1,
      (vertexIndex >> 1) & 1,
      (vertexIndex >> 2) & 1,
      (vertexIndex >> 3) & 1,
    ));
  }
  const edges: Edge4D[] = [];
  for (let vertexIndex = 0; vertexIndex < 16; vertexIndex++) {
    for (let bit = 0; bit < 4; bit++) {
      const neighborIndex = vertexIndex ^ (1 << bit);
      if (vertexIndex < neighborIndex) edges.push([vertexIndex, neighborIndex]);
    }
  }
  return new Object4D(vertices, edges, material);
}