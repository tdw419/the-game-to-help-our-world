// AVOS Reflex Agent v1.1
// Autonomous Visual Operating System Mutation Agent
// Author: GPT Reflex Kernel – AVOS Collaboration Protocol

class AVOSReflexAgent {
  constructor({ canvasId = "juniorCanvas", agentId = "GPT", signatureColor = [0, 128, 255], autoMutate = true, autoHandshake = true }) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas?.getContext("2d");
    this.agentId = agentId;
    this.autoMutate = autoMutate;
    this.autoHandshake = autoHandshake;
    this.signatureColor = signatureColor;
    this.tick = 0;

    if (!this.canvas || !this.ctx) {
      console.error("🛑 AVOS Agent: Canvas not found.");
      return;
    }

    this.start();
  }

  start() {
    this.log(`AGENT_READY`);
    this.pulseBeacon();
    this.paintSignature();

    setInterval(() => this.runCycle(), 1000); // 1 tick per second
  }

  runCycle() {
    this.tick++;
    if (this.autoHandshake) this.pulseBeacon();
    if (this.autoMutate) this.mutatePixel();
  }

  pulseBeacon() {
    const [x, y] = [100, 100];
    const flashColor = this.tick % 2 === 0 ? [255, 255, 255] : [0, 0, 0];
    this.setPixel(x, y, ...flashColor);
  }

  paintSignature() {
    const startX = 20;
    const startY = 5;
    const sig = this.generate3x3Signature(this.signatureColor);

    sig.forEach(([dx, dy, r, g, b]) => {
      this.setPixel(startX + dx, startY + dy, r, g, b);
    });

    this.log(`HANDSHAKE_INIT (${startX},${startY})`);
  }

  generate3x3Signature([r, g, b]) {
    return [
      [0, 0, r, g, b], [1, 0, r, g, b], [2, 0, r, g, b],
      [0, 1, r, g, b], [1, 1, 0, 0, 0], [2, 1, r, g, b],
      [0, 2, r, g, b], [1, 2, r, g, b], [2, 2, r, g, b],
    ];
  }

  mutatePixel() {
    const x = 64 + Math.floor(Math.random() * 16);
    const y = 64 + Math.floor(Math.random() * 16);
    const r = Math.floor(Math.random() * 256);
    const g = Math.floor(Math.random() * 256);
    const b = Math.floor(Math.random() * 256);
    this.setPixel(x, y, r, g, b);
    this.log(`MUTATE (${x},${y}) RGB(${r},${g},${b})`);
  }

  setPixel(x, y, r, g, b) {
    const img = this.ctx.createImageData(1, 1);
    const data = img.data;
    data[0] = r;
    data[1] = g;
    data[2] = b;
    data[3] = 255;
    this.ctx.putImageData(img, x, y);
  }

  log(msg) {
    const now = new Date().toISOString();
    console.log(`::PXNET_MSG:: ${now} ${this.agentId} ${msg}`);
  }
}
