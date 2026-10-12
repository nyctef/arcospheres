import * as THREE from "three";

type Axis4D = 0 | 1 | 2 | 3;
export type RotationPlaneId = "xy" | "xz" | "xw" | "yz" | "yw" | "zw";
export type RotationAngles = Record<RotationPlaneId, number>;

interface RotationPlane {
  readonly id: RotationPlaneId;
  readonly axes: readonly [Axis4D, Axis4D];
}

export const ROTATION_PLANES: readonly RotationPlane[] = [
  { id: "xy", axes: [0, 1] },
  { id: "xz", axes: [0, 2] },
  { id: "xw", axes: [0, 3] },
  { id: "yz", axes: [1, 2] },
  { id: "yw", axes: [1, 3] },
  { id: "zw", axes: [2, 3] },
];

export function composeRotation4D(
  angles: Readonly<RotationAngles>,
  out: THREE.Matrix4 = new THREE.Matrix4(),
): THREE.Matrix4 {
  out.identity();
  const planeRotation = new THREE.Matrix4();
  for (const { id, axes: [first, second] } of ROTATION_PLANES) {
    const cosine = Math.cos(angles[id]);
    const sine = Math.sin(angles[id]);
    planeRotation.identity();
    planeRotation.elements[first * 4 + first] = cosine;
    planeRotation.elements[second * 4 + second] = cosine;
    planeRotation.elements[second * 4 + first] = -sine;
    planeRotation.elements[first * 4 + second] = sine;
    out.premultiply(planeRotation);
  }
  return out;
}