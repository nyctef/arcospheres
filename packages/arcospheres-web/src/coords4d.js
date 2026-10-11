import * as THREE from "three";

/** Point that the 4th dimension is projected towards. */
export const PROJECTION_CENTER = new THREE.Vector3(0.5, 0.5, 0.5);

/** Distance parameter: a point at w is scaled by d / (d + w), so w=0 -> 1 and w=1 -> 0.5 when d=1. */
export const PROJECTION_DISTANCE = 1;

/**
 * Project a 4D point [x, y, z, w] into 3D by scaling its xyz offset from
 * `center` by a factor that shrinks as w grows.
 */
export function project4to3(
  [x, y, z, w],
  center = PROJECTION_CENTER,
  d = PROJECTION_DISTANCE,
  out = new THREE.Vector3(),
) {
  const scale = d / (d + w);
  return out.set(
    center.x + (x - center.x) * scale,
    center.y + (y - center.y) * scale,
    center.z + (z - center.z) * scale,
  );
}
