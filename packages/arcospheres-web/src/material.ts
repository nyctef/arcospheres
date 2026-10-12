import * as THREE from "three";

export interface DepthLineMaterialOptions {
  color?: THREE.ColorRepresentation;
  nearDistance?: number;
  farDistance?: number;
  nearBrightness?: number;
  farBrightness?: number;
}

export function createDepthLineMaterial({
  color = 0x44aaff,
  nearDistance = 2,
  farDistance = 6,
  nearBrightness = 1.15,
  farBrightness = 0.85,
}: DepthLineMaterialOptions = {}): THREE.ShaderMaterial {
  if (nearDistance < 0 || farDistance <= nearDistance) {
    throw new RangeError("Depth fade distances must satisfy 0 <= nearDistance < farDistance");
  }
  return new THREE.ShaderMaterial({
    uniforms: {
      color: new THREE.Uniform(new THREE.Color(color)),
      nearDistance: new THREE.Uniform(nearDistance),
      farDistance: new THREE.Uniform(farDistance),
      nearBrightness: new THREE.Uniform(nearBrightness),
      farBrightness: new THREE.Uniform(farBrightness),
    },
    vertexShader: `
      varying vec3 viewPosition;

      void main() {
        vec4 positionInView = modelViewMatrix * vec4(position, 1.0);
        viewPosition = positionInView.xyz;
        gl_Position = projectionMatrix * positionInView;
      }
    `,
    fragmentShader: `
      uniform vec3 color;
      uniform float nearDistance;
      uniform float farDistance;
      uniform float nearBrightness;
      uniform float farBrightness;
      varying vec3 viewPosition;

      void main() {
        float fade = smoothstep(nearDistance, farDistance, length(viewPosition));
        float brightness = mix(nearBrightness, farBrightness, fade);
        gl_FragColor = vec4(color * brightness, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }
    `,
  });
}