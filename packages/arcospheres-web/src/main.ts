import * as THREE from "three";
import { createCornerBillboards } from "./billboards";
import { PROJECTION_CENTER, project4to3 } from "./coords4d";
import { createDepthLineMaterial } from "./material";
import { createTesseract } from "./object4d";
import { composeRotation4D, ROTATION_PLANES } from "./rotation4d";
import type { RotationAngles } from "./rotation4d";
(function (window: Window): void {
  const viewport = document.getElementById("viewport");
  const controls = document.getElementById("rotation-controls");
  const resetButton = document.querySelector<HTMLButtonElement>("#reset-rotation");
  if (viewport === null || controls === null || resetButton === null) {
    throw new Error("Missing tesseract viewport or rotation controls");
  }
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 100);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  viewport.appendChild(renderer.domElement);

  const tesseract = createTesseract(createDepthLineMaterial());
  scene.add(tesseract.object3d);
  const billboards = createCornerBillboards(tesseract.vertices);
  for (const { sprite } of billboards) {
    scene.add(sprite);
  }

  const target = PROJECTION_CENTER;
  const viewDirection = new THREE.Vector3(2, 1, 3).normalize();

  const center4d = new THREE.Vector4(0.5, 0.5, 0.5, 0.5);
  const rotation4d = new THREE.Matrix4();
  const angles: RotationAngles = { xy: 0, xz: 0, xw: 0, yz: 0, yw: 0, zw: 0 };
  const rotatingVertices = tesseract.vertices.map((vertex) => ({
    vertex,
    offset: vertex.clone().sub(center4d),
  }));

  function render(): void {
    composeRotation4D(angles, rotation4d);
    for (const { vertex, offset } of rotatingVertices) {
      vertex.copy(offset).applyMatrix4(rotation4d).add(center4d);
    }
    tesseract.updateProjection();
    for (const { vertex, sprite } of billboards) {
      project4to3(vertex, undefined, undefined, sprite.position);
    }
    renderer.render(scene, camera);
  }

  const sliders = ROTATION_PLANES.map(({ id }) => {
    const row = document.createElement("div");
    row.className = "rotation-control";
    const label = document.createElement("label");
    label.htmlFor = `rotation-${id}`;
    label.textContent = id.toUpperCase();
    const output = document.createElement("output");
    output.htmlFor = `rotation-${id}`;
    output.value = "0\u00b0";
    const input = document.createElement("input");
    input.type = "range";
    input.id = label.htmlFor;
    input.min = "-180";
    input.max = "180";
    input.step = "1";
    input.value = "0";
    let dragging = false;
    input.addEventListener("pointerdown", (): void => { dragging = true; });
    window.addEventListener("pointerup", (): void => { dragging = false; });
    window.addEventListener("pointercancel", (): void => { dragging = false; });
    input.addEventListener("input", (): void => {
      const degrees = dragging && Math.abs(input.valueAsNumber) <= 10 ? 0 : input.valueAsNumber;
      input.value = String(degrees);
      angles[id] = THREE.MathUtils.degToRad(degrees);
      output.value = `${degrees}\u00b0`;
      render();
    });
    row.append(label, output, input);
    controls.appendChild(row);
    return { id, input, output };
  });

  resetButton.addEventListener("click", (): void => {
    for (const { id, input, output } of sliders) {
      angles[id] = 0;
      input.value = "0";
      output.value = "0\u00b0";
    }
    render();
  });

  const resizeObserver = new ResizeObserver((): void => {
    const width = Math.max(1, viewport.clientWidth);
    const height = Math.max(1, viewport.clientHeight);
    camera.aspect = width / height;
    const distance = Math.max(
      Math.sqrt(14),
      1.35 / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) / Math.min(camera.aspect, 1),
    );
    camera.position.copy(viewDirection).multiplyScalar(distance).add(target);
    camera.lookAt(target);
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
    render();
  });
  resizeObserver.observe(viewport);
})(window);