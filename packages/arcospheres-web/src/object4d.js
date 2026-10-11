import * as THREE from "three";
import { project4to3 } from "./coords4d.js";

/** A wireframe 4D object: 4D vertices plus edges (pairs of vertex indices). */
export class Object4D {
  constructor(vertices, edges, material) {
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
  updateProjection() {
    const attr = this.object3d.geometry.getAttribute("position");
    const v = new THREE.Vector3();
    let i = 0;
    for (const [a, b] of this.edges) {
      for (const idx of [a, b]) {
        project4to3(this.vertices[idx], undefined, undefined, v);
        attr.setXYZ(i++, v.x, v.y, v.z);
      }
    }
    attr.needsUpdate = true;
  }
}

/** Unit tesseract with vertices at every combination of 0/1 in x,y,z,w. */
export function createTesseract(material) {
  const vertices = [];
  for (let i = 0; i < 16; i++) {
    vertices.push([i & 1, (i >> 1) & 1, (i >> 2) & 1, (i >> 3) & 1]);
  }
  const edges = [];
  for (let i = 0; i < 16; i++) {
    for (let bit = 0; bit < 4; bit++) {
      const j = i ^ (1 << bit);
      if (i < j) edges.push([i, j]);
    }
  }
  return new Object4D(vertices, edges, material);
}
