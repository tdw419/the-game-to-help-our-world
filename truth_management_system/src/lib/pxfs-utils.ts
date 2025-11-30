export interface MockPxfsItem {
  name: string;
  hash: string;
  isDirectory: boolean;
  type?: 'text' | 'image' | 'code' | 'folder' | 'unknown';
  children?: MockPxfsItem[];
}

export const mockPxfsRoot: MockPxfsItem = {
  name: "PXOS Root",
  hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", // Example SHA256
  isDirectory: true,
  children: [
    {
      name: "documents",
      hash: "a1a2a3a4a5a6a7a8a9a0b1b2b3b4b5b6c7c8c9c0d1d2d3d4d5d6d7d8d9e0e1e2",
      isDirectory: true,
      children: [
        { name: "report.pdf", hash: "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd", isDirectory: false, type: "text" },
        { name: "memo.docx", hash: "fedcba0987654321fedcba0987654321fedcba0987654321fedcba09876543", isDirectory: false, type: "text" },
        {
          name: "archive",
          hash: "a0b1c2d3e4f5a0b1c2d3e4f5a0b1c2d3e4f5a0b1c2d3e4f5a0b1c2d3e4f5a0b1",
          isDirectory: true,
          children: [
            { name: "old_project.zip", hash: "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff", isDirectory: false, type: "code" },
            { name: "legacy_data.tar", hash: "ffeeddccbbaa99887766554433221100ffeeddccbbaa99887766554433221100", isDirectory: false, type: "unknown" },
          ]
        },
        { name: "plan.txt", hash: "b0c1d2e3f4a5b0c1d2e3f4a5b0c1d2e3f4a5b0c1d2e3f4a5b0c1d2e3f4a5b0c1", isDirectory: false, type: "text" },
      ]
    },
    {
      name: "photos",
      hash: "f1f2f3f4f5f6f7f8f9f0a1a2a3a4a5a6b7b8b9b0c1c2c3c4c5c6c7c8c9d0d1d2",
      isDirectory: true,
      children: [
        { name: "vacation.jpg", hash: "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d", isDirectory: false, type: "image" },
        { name: "selfie.png", hash: "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789", isDirectory: false, type: "image" },
        { name: "thumbnails", hash: "9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba", isDirectory: true, children: [] },
      ]
    },
    { name: "README.md", hash: "aaaaabbbbbcccccdddddeeeeefffff0123456789abcdeffaaaaabbbbbcccccdddddeeeeefffff0123456789abcdeff", isDirectory: false, type: "text" },
    { name: "app.ts", hash: "1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1d2c3b4a5f6e7d8c9b0a1f2e", isDirectory: false, type: "code" },
  ]
};

// Helper function to convert a SHA256 hash string into an RGB color string.
// This is a simplified visualization to represent the "color" of a pixel.
// Takes the first 6 hex characters and converts them to R, G, B values.
export const hashToRgb = (hash: string): string => {
  if (!hash || hash.length < 6) {
    return 'rgb(128, 128, 128)'; // Default to gray for invalid/short hashes
  }
  const r = parseInt(hash.substring(0, 2), 16);
  const g = parseInt(hash.substring(2, 4), 16);
  const b = parseInt(hash.substring(4, 6), 16);
  return `rgb(${r}, ${g}, ${b})`;
};