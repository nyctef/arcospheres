import * as THREE from "three";
import { project4to3 } from "./coords4d";
import { createDepthSpriteMaterial } from "./material";

export interface CornerLabel {
  readonly label: string;
  readonly vertexIndex: number;
}

export const CORNER_LABELS: readonly CornerLabel[] = [
  { label: "\u03be", vertexIndex: 1 },
  { label: "\u03b3", vertexIndex: 2 },
  { label: "\u03b6", vertexIndex: 4 },
  { label: "\u03c6", vertexIndex: 8 },
  { label: "\u03bb", vertexIndex: 7 },
  { label: "\u03b8", vertexIndex: 13 },
  { label: "\u03b5", vertexIndex: 14 },
  { label: "\u03c9", vertexIndex: 11 },
];

export interface CornerBillboard {
  readonly vertex: THREE.Vector4;
  readonly sprite: THREE.Sprite;
}

export function createCornerBillboards(vertices: readonly THREE.Vector4[]): readonly CornerBillboard[] {
  return CORNER_LABELS.map(({ label, vertexIndex }): CornerBillboard => {
    const vertex = vertices[vertexIndex];
    if (vertex === undefined) {
      throw new RangeError(`Label references missing vertex ${vertexIndex}`);
    }
    const canvas = document.createElement("canvas");
    canvas.width = 128;
    canvas.height = 128;
    const context = canvas.getContext("2d");
    if (context === null) {
      throw new Error("Cannot create corner label canvas");
    }
    context.beginPath();
    context.arc(64, 64, 58, 0, Math.PI * 2);
    context.fillStyle = "#e6f4ff";
    context.fill();
    context.lineWidth = 4;
    context.strokeStyle = "#44aaff";
    context.stroke();
    const labelCanvas = document.createElement("canvas");
    labelCanvas.width = 128;
    labelCanvas.height = 128;
    const labelContext = labelCanvas.getContext("2d");
    if (labelContext === null) {
      throw new Error("Cannot create corner label mask");
    }
    labelContext.font = "80px Georgia, serif";
    labelContext.textAlign = "center";
    labelContext.textBaseline = "middle";
    labelContext.fillStyle = "#102333";
    labelContext.fillText(label, 64, 64);
    context.drawImage(labelCanvas, 0, 0);

    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const labelMask = new THREE.CanvasTexture(labelCanvas);
    const material = createDepthSpriteMaterial(texture, labelMask);
    const sprite = new THREE.Sprite(material);
    sprite.name = label;
    sprite.scale.set(0.16, 0.16, 1);
    project4to3(vertex, undefined, undefined, sprite.position);
    return { vertex, sprite };
  });
}