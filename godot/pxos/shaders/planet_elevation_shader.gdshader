// shaders/planet_elevation_shader.gdshader
shader_type spatial;
render_mode unshaded; // For simplicity, just show color and displacement

uniform sampler2D color_map : hint_albedo; // Our data_layer (RGB from map.py)
uniform sampler2D elevation_map : hint_normal; // Our elevation_layer (Alpha from map.py)

uniform float height_scale = 10.0; // How much to displace vertices by elevation
uniform float texture_scale = 1.0; // Scale UVs if mesh doesn't match texture aspect ratio

void vertex() {
    // Read elevation from the elevation_map texture (grayscale)
    // We sample UV based on the vertex position (x, z) because PlaneMesh is XZ plane
    vec2 uv = VERTEX.xz * texture_scale; // Assuming PlaneMesh is centered at (0,0)

    // Normalize UV to 0-1 range for texture sampling, assuming the mesh is 1x1 unit
    uv = (uv + 0.5) * 0.5; // If vertex spans -0.5 to 0.5, convert to 0 to 1

    // Sample the elevation map. .r because it's grayscale (L8 format).
    float elevation = texture(elevation_map, uv).r; 

    // Displace the vertex along the Y-axis based on elevation
    // Subtract 0.5 to center displacement around the plane's original height if needed
    VERTEX.y += (elevation - 0.5) * height_scale; 

    // For spherical projection:
    // This shader is for a PlaneMesh. For a SphereMesh, displacement is along normal.
    // If using SphereMesh:
    // VERTEX += NORMAL * (elevation - 0.5) * height_scale;
}

void fragment() {
    // Get UV from vertex shader output (Godot handles passing UV_LIGHTMAP etc.)
    // For a PlaneMesh with default UVs (0-1 across its surface), we can use UV directly.
    vec2 uv = UV;
    
    // Sample color from the color_map (our data_layer)
    ALBEDO = texture(color_map, uv).rgb;
}