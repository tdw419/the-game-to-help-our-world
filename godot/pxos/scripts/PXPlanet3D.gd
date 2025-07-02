# scripts/PXPlanet3D.gd
extends Node3D

class_name PXPlanet3D

@onready var terrain_mesh: MeshInstance3D = $TerrainMesh

func _ready():
    # Ensure the material is a ShaderMaterial
    if terrain_mesh.get_surface_override_material(0) is ShaderMaterial:
        print("PXPlanet3D: ShaderMaterial found on TerrainMesh.")
    else:
        push_error("PXPlanet3D: TerrainMesh does not have a ShaderMaterial assigned!")


# This function will be called by PXGPUDriver to update the textures
func update_textures(color_texture: Texture2D, elevation_texture: Texture2D):
    if terrain_mesh.get_surface_override_material(0) is ShaderMaterial:
        var material = terrain_mesh.get_surface_override_material(0) as ShaderMaterial
        material.set_shader_parameter("color_map", color_texture)
        material.set_shader_parameter("elevation_map", elevation_texture)
        # print("PXPlanet3D: Textures updated.")
    else:
        push_error("PXPlanet3D: Cannot update textures, ShaderMaterial not found.")

# Optional: Add a simple camera controller
func _process(delta):
    # Example: Simple camera rotation around the planet
    var rotation_speed = 0.1
    # Rotate the root Node3D to rotate the whole planet and camera
    rotation_degrees.y += rotation_speed * delta