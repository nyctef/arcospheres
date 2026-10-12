import * as THREE from "three";
import { PROJECTION_CENTER } from "./coords4d";
import { createTesseract } from "./object4d";
(function (window: Window): void {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  document.body.appendChild(renderer.domElement);

  const tesseract = createTesseract(new THREE.LineBasicMaterial({ color: 0x44aaff }));
  scene.add(tesseract.object3d);

  const target = PROJECTION_CENTER;
  const orbitRadius = 3;

  window.addEventListener("resize", (): void => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  renderer.setAnimationLoop((time: number): void => {
    const angle = time * 0.0005;
    camera.position.set(
      target.x + Math.sin(angle) * orbitRadius,
      target.y + 1,
      target.z + Math.cos(angle) * orbitRadius,
    );
    camera.lookAt(target);
    renderer.render(scene, camera);
  });
})(window);