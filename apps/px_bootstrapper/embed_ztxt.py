import os

def embed_ztxt(file_path, output_path):
    with open(file_path, "rb") as f:
        data = f.read()
    with open(output_path, "w") as f:
        f.write(f"{os.path.basename(file_path).replace('.', '_')}:\n")
        for i, byte in enumerate(data):
            if i % 16 == 0:
                f.write("    db ")
            f.write(f"0x{byte:02x}")
            if i < len(data) - 1:
                f.write(", ")
            if i % 16 == 15:
                f.write("\n")
        f.write("\n")

# Embed all zTXt files
files = ["pxruntime.ztxt", "pxboot.ztxt", "PX_UPGRADE.pxexe", "pxexecutor.pxmod", "PXOS.config.json"]
for file in files:
    embed_ztxt(file, f"{file}.bin")