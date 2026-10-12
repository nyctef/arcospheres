import * as THREE from "three";

export interface DepthFadeOptions {
  nearDistance?: number;
  farDistance?: number;
  nearBrightness?: number;
  farBrightness?: number;
}

export interface DepthLineMaterialOptions extends DepthFadeOptions {
  color?: THREE.ColorRepresentation;
}

interface DepthFadeUniforms {
  nearDistance: THREE.Uniform<number>;
  farDistance: THREE.Uniform<number>;
  nearBrightness: THREE.Uniform<number>;
  farBrightness: THREE.Uniform<number>;
}

const DEPTH_FADE_SHADER = `
  uniform float nearDistance;
  uniform float farDistance;
  uniform float nearBrightness;
  uniform float farBrightness;

  float getDepthBrightness(vec3 positionInView) {
    float fade = smoothstep(nearDistance, farDistance, length(positionInView));
    return mix(nearBrightness, farBrightness, fade);
  }
`;

function createDepthFadeUniforms({
  nearDistance = 2,
  farDistance = 4,
  nearBrightness = 2,
  farBrightness = 0.2,
}: DepthFadeOptions): DepthFadeUniforms {
  if (nearDistance < 0 || farDistance <= nearDistance) {
    throw new RangeError("Depth fade distances must satisfy 0 <= nearDistance < farDistance");
  }
  return {
    nearDistance: new THREE.Uniform(nearDistance),
    farDistance: new THREE.Uniform(farDistance),
    nearBrightness: new THREE.Uniform(nearBrightness),
    farBrightness: new THREE.Uniform(farBrightness),
  };
}

export function createDepthLineMaterial({
  color = 0x44aaff,
  ...depthFade
}: DepthLineMaterialOptions = {}): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    uniforms: {
      color: new THREE.Uniform(new THREE.Color(color)),
      ...createDepthFadeUniforms(depthFade),
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
      ${DEPTH_FADE_SHADER}
      varying vec3 viewPosition;

      void main() {
        float brightness = getDepthBrightness(viewPosition);
        gl_FragColor = vec4(color * brightness, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }
    `,
  });
}

export function createDepthSpriteMaterial(
  map: THREE.Texture,
  labelMask: THREE.Texture,
  options: DepthFadeOptions = {},
): THREE.SpriteMaterial {
  const uniforms = createDepthFadeUniforms(options);
  const material = new THREE.SpriteMaterial({ map, depthWrite: false, toneMapped: false });
  material.onBeforeCompile = (shader): void => {
    Object.assign(shader.uniforms, uniforms, { labelMask: new THREE.Uniform(labelMask) });
    shader.vertexShader = `varying vec3 viewPosition;\n${shader.vertexShader}`.replace(
      "gl_Position = projectionMatrix * mvPosition;",
      "viewPosition = mvPosition.xyz;\ngl_Position = projectionMatrix * mvPosition;",
    );
    shader.fragmentShader = `
      varying vec3 viewPosition;
      uniform sampler2D labelMask;
      ${DEPTH_FADE_SHADER}
      ${shader.fragmentShader}
    `.replace(
      "#include <map_fragment>",
      `#include <map_fragment>
       float labelCoverage = texture2D(labelMask, vMapUv).a;
       float brightness = getDepthBrightness(viewPosition);
       diffuseColor.rgb *= mix(brightness, 1.0, labelCoverage);`,
    );
  };
  material.customProgramCacheKey = (): string => "depth-sprite-v1";
  return material;
}