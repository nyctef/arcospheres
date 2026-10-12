import * as THREE from "three";
import { PROJECTION_CENTER } from "./coords4d";
import { createDepthLineMaterial } from "./material";
import { createTesseract } from "./object4d";
(function (window: Window): void {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  document.body.appendChild(renderer.domElement);

  const tesseract = createTesseract(createDepthLineMaterial());
  scene.add(tesseract.object3d);

  const target = PROJECTION_CENTER;
  camera.position.set(target.x + 2, target.y + 1, target.z + 3);
  camera.lookAt(target);

  const center4d = new THREE.Vector4(0.5, 0.5, 0.5, 0.5);
  const rotation4d = new THREE.Matrix4();
  const rotatingVertices = tesseract.vertices.map((vertex) => ({
    vertex,
    offset: vertex.clone().sub(center4d),
  }));

  window.addEventListener("resize", (): void => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  renderer.setAnimationLoop((time: number): void => {
    const angle = time * 0.0005;
    const cosine = Math.cos(angle);
    const sine = Math.sin(angle);
    rotation4d.set(
      cosine, 0, 0, -sine,
      0, 1, 0, 0,
      0, 0, 1, 0,
      sine, 0, 0, cosine,
    );
    for (const { vertex, offset } of rotatingVertices) {
      vertex.copy(offset).applyMatrix4(rotation4d).add(center4d);
    }
    tesseract.updateProjection();
    renderer.render(scene, camera);
  });
})(window);