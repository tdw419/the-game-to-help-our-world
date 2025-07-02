// shaders/pxos_opcode_shader.gdshader
shader_type canvas_item;

uniform sampler2D px_buffer;
uniform sampler2D px_font_atlas;
uniform sampler2D injection_overlay;
uniform sampler2D px_data_read_buffer;
uniform sampler2D pxnet_bus_buffer; // NEW: PXNet communication bus
uniform float time;
uniform vec2 pxos_resolution;

const float PX_NO_OP_ID       = 0.0 / 255.0;
const float PX_DRAW_PIXEL_ID  = 1.0 / 255.0;
const float PX_DRAW_CHAR_ID   = 2.0 / 255.0;
const float PX_DRAW_LINE_SEGMENT_ID = 3.0 / 255.0;
const float PX_DRAW_RECT_ID   = 4.0 / 255.0;
const float PX_COPY_REGION_ID = 5.0 / 255.0;
const float PX_READ_DATA_TO_COLOR_ID = 6.0 / 255.0;

// PXNet Message Types - Re-define for shader (cannot access GDScript constants directly)
const float PXNET_MESSAGE_TYPE_NONE_SHADER = 0.0 / 255.0;
const float PXNET_MESSAGE_TYPE_ECHO_SHADER = 11.0 / 255.0;
const float PXNET_MESSAGE_TYPE_CMD_DRAW_PIXEL_SHADER = 12.0 / 255.0;


const float FONT_CHAR_WIDTH  = 5.0;
const float FONT_CHAR_HEIGHT = 5.0;
const float FONT_ATLAS_CHARS_PER_ROW = 16.0;

const float MAX_LINE_OFFSET = 20.0; 
const float LINE_CHECK_NEIGHBORHOOD = MAX_LINE_OFFSET + 1.0; 

const float MAX_RECT_DIMENSION = 20.0; 
const float RECT_CHECK_NEIGHBORHOOD = MAX_RECT_DIMENSION + 1.0;

const float COPY_REGION_WIDTH = 4.0;
const float COPY_REGION_HEIGHT = 4.0;
const float COPY_CHECK_NEIGHBORHOOD = max(COPY_REGION_WIDTH, COPY_REGION_HEIGHT) + 1.0;

bool is_on_segment(vec2 p, vec2 a, vec2 b, float tolerance) {
    float dist_sq_ab = distance_squared(a, b);
    if (dist_sq_ab < 0.001) {
        return distance_squared(p, a) < tolerance * tolerance;
    }
    float t = dot(p - a, b - a) / dist_sq_ab;
    t = clamp(t, 0.0, 1.0);
    vec2 projection = a + t * (b - a);
    return distance_squared(p, projection) < tolerance * tolerance;
}

bool is_in_rect(vec2 p, vec2 o, vec2 s) {
    return p.x >= o.x && p.x < o.x + s.x &&
           p.y >= o.y && p.y < o.y + s.y;
}


void fragment() {
    vec2 current_px_coord = floor(FRAGCOORD.xy);
    vec2 uv_normalized = current_px_coord / pxos_resolution;

    vec4 current_pixel_state = texture(px_buffer, uv_normalized);
    vec4 out_color = current_pixel_state; 

    // --- Process Injection Commands First ---
    vec4 injected_data = texture(injection_overlay, uv_normalized);
    bool processed_by_injection = false;

    if (injected_data.a > 0.1) {
        float injected_opcode_id = injected_data.r;
        
        if (abs(injected_opcode_id - PX_DRAW_PIXEL_ID) < 0.001) {
            out_color = vec4(injected_data.g, injected_data.b, 0.0, 1.0);
            processed_by_injection = true;
        } else if (abs(injected_opcode_id - PX_DRAW_CHAR_ID) < 0.001) {
            bool drawn_by_injected_char = false;
            for (float y_offset = -(FONT_CHAR_HEIGHT - 1.0); y_offset <= 0.0; y_offset += 1.0) {
                for (float x_offset = -(FONT_CHAR_WIDTH - 1.0); x_offset <= 0.0; x_offset += 1.0) {
                    vec2 potential_injected_opcode_px_coord = current_px_coord + vec2(x_offset, y_offset);
                    vec2 potential_injected_opcode_uv = potential_injected_opcode_px_coord / pxos_resolution;

                    if (potential_injected_opcode_px_coord.x >= 0.0 && potential_injected_opcode_px_coord.x < pxos_resolution.x &&
                        potential_injected_opcode_px_coord.y >= 0.0 && potential_injected_opcode_px_coord.y < pxos_resolution.y) {
                        
                        vec4 check_injected_data = texture(injection_overlay, potential_injected_opcode_uv);
                        if (check_injected_data.a > 0.1 && abs(check_injected_data.r - PX_DRAW_CHAR_ID) < 0.001) {
                            float current_char_index = floor(check_injected_data.g * 255.0);
                            float current_char_color_val = check_injected_data.b;

                            vec2 local_offset_from_injected_char_anchor = current_px_coord - potential_injected_opcode_px_coord;
                            
                            float current_char_in_row = mod(current_char_index, FONT_ATLAS_CHARS_PER_ROW);
                            float current_char_row = floor(current_char_index / FONT_ATLAS_CHARS_PER_ROW);

                            vec2 current_font_src_uv_start = vec2(current_char_in_row * FONT_CHAR_WIDTH, current_char_row * FONT_CHAR_HEIGHT);
                            vec2 current_font_src_uv_current = current_font_src_uv_start + local_offset_from_injected_char_anchor;
                            
                            vec2 font_atlas_size = vec2(textureSize(px_font_atlas, 0));
                            vec4 font_pixel = texture(px_font_atlas, current_font_src_uv_current / font_atlas_size);

                            if (font_pixel.a > 0.1) { 
                                out_color = vec4(current_char_color_val, current_char_color_val, current_char_color_val, 1.0);
                                drawn_by_injected_char = true;
                                processed_by_injection = true;
                                break;
                            }
                        }
                    }
                }
                if (drawn_by_injected_char) {
                    break;
                }
            }
        } 
        else if (abs(injected_opcode_id - PX_DRAW_LINE_SEGMENT_ID) < 0.001) {
            bool drawn_by_injected_line = false;
            for (float y_k = -LINE_CHECK_NEIGHBORHOOD; y_k <= LINE_CHECK_NEIGHBORHOOD; y_k += 1.0) {
                for (float x_k = -LINE_CHECK_NEIGHBORHOOD; x_k <= LINE_CHECK_NEIGHBORHOOD; x_k += 1.0) {
                    vec2 potential_line_opcode_px_coord = current_px_coord + vec2(x_k, y_k);
                    vec2 potential_line_opcode_uv = potential_line_opcode_px_coord / pxos_resolution;

                    if (potential_line_opcode_px_coord.x >= 0.0 && potential_line_opcode_px_coord.x < pxos_resolution.x &&
                        potential_line_opcode_px_coord.y >= 0.0 && potential_line_opcode_px_coord.y < pxos_resolution.y) {

                        vec4 check_injected_line_data = texture(injection_overlay, potential_line_opcode_uv);
                        if (check_injected_line_data.a > 0.1 && abs(check_injected_line_data.r - PX_DRAW_LINE_SEGMENT_ID) < 0.001) {
                            float dx_val = floor(check_injected_line_data.g * 255.0);
                            float dy_val = floor(check_injected_line_data.b * 255.0);

                            dx_val = min(dx_val, MAX_LINE_OFFSET);
                            dy_val = min(dy_val, MAX_LINE_OFFSET);
                            
                            vec2 p0 = potential_line_opcode_px_coord;
                            vec2 p1 = p0 + vec2(dx_val, dy_val);

                            if (is_on_segment(current_px_coord, p0, p1, 0.8)) {
                                out_color = vec4(1.0, 1.0, 1.0, 1.0);
                                drawn_by_injected_line = true;
                                processed_by_injection = true;
                                break;
                            }
                        }
                    }
                }
                if (drawn_by_injected_line) {
                    break;
                }
            }
        }
        else if (abs(injected_opcode_id - PX_DRAW_RECT_ID) < 0.001) {
            bool drawn_by_injected_rect = false;
            for (float y_k = -RECT_CHECK_NEIGHBORHOOD; y_k <= 0.0; y_k += 1.0) {
                for (float x_k = -RECT_CHECK_NEIGHBORHOOD; x_k <= 0.0; x_k += 1.0) {
                    vec2 potential_rect_opcode_px_coord = current_px_coord + vec2(x_k, y_k);
                    vec2 potential_rect_opcode_uv = potential_rect_opcode_px_coord / pxos_resolution;

                     if (potential_rect_opcode_px_coord.x >= 0.0 && potential_rect_opcode_px_coord.x < pxos_resolution.x &&
                        potential_rect_opcode_px_coord.y >= 0.0 && potential_rect_opcode_px_coord.y < pxos_resolution.y) {

                        vec4 check_injected_rect_data = texture(injection_overlay, potential_rect_opcode_uv);
                        if (check_injected_rect_data.a > 0.1 && abs(check_injected_rect_data.r - PX_DRAW_RECT_ID) < 0.001) {
                            float rect_width = floor(check_injected_rect_data.g * 255.0);
                            float rect_height = floor(check_injected_rect_data.b * 255.0);
                            
                            rect_width = min(rect_width, MAX_RECT_DIMENSION);
                            rect_height = min(rect_height, MAX_RECT_DIMENSION);

                            if (is_in_rect(current_px_coord, potential_rect_opcode_px_coord, vec2(rect_width, rect_height))) {
                                out_color = vec4(0.0, 0.0, 1.0, 1.0);
                                drawn_by_injected_rect = true;
                                processed_by_injection = true;
                                break;
                            }
                        }
                    }
                }
                if (drawn_by_injected_rect) {
                    break;
                }
            }
        }
        else if (abs(injected_opcode_id - PX_COPY_REGION_ID) < 0.001) {
            bool drawn_by_injected_copy = false;
            for (float y_k = -COPY_CHECK_NEIGHBORHOOD; y_k <= 0.0; y_k += 1.0) {
                for (float x_k = -COPY_CHECK_NEIGHBORHOOD; x_k <= 0.0; x_k += 1.0) {
                    vec2 potential_copy_opcode_px_coord = current_px_coord + vec2(x_k, y_k);
                    vec2 potential_copy_opcode_uv = potential_copy_opcode_px_coord / pxos_resolution;

                    if (potential_copy_opcode_px_coord.x >= 0.0 && potential_copy_opcode_px_coord.x < pxos_resolution.x &&
                        potential_copy_opcode_px_coord.y >= 0.0 && potential_copy_opcode_px_coord.y < pxos_resolution.y) {

                        vec4 check_injected_copy_data = texture(injection_overlay, potential_copy_opcode_uv);
                        if (check_injected_copy_data.a > 0.1 && abs(check_injected_copy_data.r - PX_COPY_REGION_ID) < 0.001) {
                            float src_offset_x = floor(check_injected_copy_data.g * 255.0);
                            float src_offset_y = floor(check_injected_copy_data.b * 255.0);
                            
                            src_offset_x = (src_offset_x / 255.0) * (2.0 * MAX_RECT_DIMENSION) - MAX_RECT_DIMENSION;
                            src_offset_y = (src_offset_y / 255.0) * (2.0 * MAX_RECT_DIMENSION) - MAX_RECT_DIMENSION;


                            if (is_in_rect(current_px_coord, potential_copy_opcode_px_coord, vec2(COPY_REGION_WIDTH, COPY_REGION_HEIGHT))) {
                                vec2 local_dest_coord = current_px_coord - potential_copy_opcode_px_coord;
                                vec2 source_px_coord = potential_copy_opcode_px_coord + vec2(src_offset_x, src_offset_y) + local_dest_coord;
                                vec2 source_uv = source_px_coord / pxos_resolution;

                                out_color = texture(px_buffer, source_uv);
                                drawn_by_injected_copy = true;
                                processed_by_injection = true;
                                break;
                            }
                        }
                    }
                }
                if (drawn_by_injected_copy) {
                    break;
                }
            }
        }
        else if (abs(injected_opcode_id - PX_READ_DATA_TO_COLOR_ID) < 0.001) {
            out_color = texture(px_data_read_buffer, uv_normalized);
            processed_by_injection = true;
        }

        if (!processed_by_injection) {
            out_color = injected_data;
            processed_by_injection = true;
        }
    } 


    // --- Process PXNet Bus for Commands ---
    // Read the message from the PXNet bus (e.g., at (0,0) of the bus)
    vec4 pxnet_message = texture(pxnet_bus_buffer, vec2(0.0, 0.0));
    float pxnet_message_type = pxnet_message.r;

    // Example: If PXNet bus sends a PXNET_MESSAGE_TYPE_CMD_DRAW_PIXEL
    if (abs(pxnet_message_type - PXNET_MESSAGE_TYPE_CMD_DRAW_PIXEL_SHADER) < 0.001) {
        // The message's G & B channels contain the target (x,y) to draw
        float target_x_msg = floor(pxnet_message.g * 255.0);
        float target_y_msg = floor(pxnet_message.b * 255.0);
        
        // The message's A channel could contain the color or agent ID. Let's use current time for a changing color.
        vec4 draw_color = vec4(sin(time*5.0)*0.5 + 0.5, cos(time*3.0)*0.5 + 0.5, sin(time*7.0)*0.5 + 0.5, 1.0); // Dynamic color

        // If the current pixel is the target specified by the PXNet message
        if (distance(current_px_coord, vec2(target_x_msg, target_y_msg)) < 0.5) { // Check for exact match
            out_color = draw_color; // Draw the pixel
        }
    }


    // --- Only Process Normal PX_BUFFER Opcode Execution if no injection or PXNet command was processed ---
    if (!processed_by_injection && abs(pxnet_message.a) < 0.001) { // Only if no injection and no active PXNet command
        float opcode_id = current_pixel_state.r; 

        if (abs(opcode_id - PX_NO_OP_ID) < 0.001) {
            // No change
        } else if (abs(opcode_id - PX_DRAW_PIXEL_ID) < 0.001) {
            out_color = vec4(current_pixel_state.g, current_pixel_state.b, 0.0, 1.0);
        } else if (abs(opcode_id - PX_DRAW_CHAR_ID) < 0.001) {
            bool drawn_by_self_char = false;
            for (float y_offset = -(FONT_CHAR_HEIGHT - 1.0); y_offset <= 0.0; y_offset += 1.0) {
                for (float x_offset = -(FONT_CHAR_WIDTH - 1.0); x_offset <= 0.0; x_offset += 1.0) {
                    vec2 potential_opcode_px_coord = current_px_coord + vec2(x_offset, y_offset);
                    vec2 potential_opcode_uv = potential_opcode_px_coord / pxos_resolution;

                    if (potential_opcode_px_coord.x >= 0.0 && potential_opcode_px_coord.x < pxos_resolution.x &&
                        potential_opcode_px_coord.y >= 0.0 && potential_opcode_px_coord.y < pxos_resolution.y) {
                        
                        vec4 potential_opcode_pixel_data = texture(px_buffer, potential_opcode_uv);
                        float potential_opcode_id = potential_opcode_pixel_data.r;

                        if (abs(potential_opcode_id - PX_DRAW_CHAR_ID) < 0.001) {
                            float char_index = floor(potential_opcode_pixel_data.g * 255.0);
                            float char_color_val = potential_opcode_pixel_data.b;

                            vec2 local_char_pixel_coord = current_px_coord - potential_opcode_px_coord;
                            
                            float char_in_row = mod(char_index, FONT_ATLAS_CHARS_PER_ROW);
                            float char_row = floor(char_index / FONT_ATLAS_CHARS_PER_ROW);

                            vec2 font_src_uv_start = vec2(char_in_row * FONT_CHAR_WIDTH, char_row * FONT_CHAR_HEIGHT);
                            vec2 font_src_uv_current = font_src_uv_start + local_char_pixel_coord;
                            
                            vec2 font_atlas_size = vec2(textureSize(px_font_atlas, 0));
                            vec4 font_pixel = texture(px_font_atlas, current_font_src_uv_current / font_atlas_size);

                            if (font_pixel.a > 0.1) { 
                                out_color = vec4(char_color_val, char_color_val, char_color_val, 1.0);
                                drawn_by_self_char = true;
                                break;
                            }
                        }
                    }
                }
                if (drawn_by_self_char) {
                    break;
                }
            }
        }
        else if (abs(opcode_id - PX_DRAW_LINE_SEGMENT_ID) < 0.001) {
            bool drawn_by_self_line = false;
            for (float y_k = -LINE_CHECK_NEIGHBORHOOD; y_k <= LINE_CHECK_NEIGHBORHOOD; y_k += 1.0) {
                for (float x_k = -LINE_CHECK_NEIGHBORHOOD; x_k <= LINE_CHECK_NEIGHBORHOOD; x_k += 1.0) {
                    vec2 potential_line_opcode_px_coord = current_px_coord + vec2(x_k, y_k);
                    vec2 potential_line_opcode_uv = potential_line_opcode_px_coord / pxos_resolution;

                    if (potential_line_opcode_px_coord.x >= 0.0 && potential_line_opcode_px_coord.x < pxos_resolution.x &&
                        potential_line_opcode_px_coord.y >= 0.0 && potential_line_opcode_px_coord.y < pxos_resolution.y) {

                        vec4 check_line_data = texture(px_buffer, potential_line_opcode_uv);
                        if (abs(check_line_data.r - PX_DRAW_LINE_SEGMENT_ID) < 0.001) {
                            float dx_val = floor(check_line_data.g * 255.0);
                            float dy_val = floor(check_line_data.b * 255.0);
                            
                            dx_val = min(dx_val, MAX_LINE_OFFSET);
                            dy_val = min(dy_val, MAX_LINE_OFFSET);

                            vec2 p0 = potential_line_opcode_px_coord;
                            vec2 p1 = p0 + vec2(dx_val, dy_val);

                            if (is_on_segment(current_px_coord, p0, p1, 0.8)) {
                                out_color = vec4(1.0, 1.0, 1.0, 1.0);
                                drawn_by_self_line = true;
                                break;
                            }
                        }
                    }
                }
                if (drawn_by_self_line) {
                    break;
                }
            }
        }
        else if (abs(opcode_id - PX_DRAW_RECT_ID) < 0.001) {
            bool drawn_by_self_rect = false;
            for (float y_k = -RECT_CHECK_NEIGHBORHOOD; y_k <= 0.0; y_k += 1.0) {
                for (float x_k = -RECT_CHECK_NEIGHBORHOOD; x_k <= 0.0; x_k += 1.0) {
                    vec2 potential_rect_opcode_px_coord = current_px_coord + vec2(x_k, y_k);
                    vec2 potential_rect_opcode_uv = potential_rect_opcode_px_coord / pxos_resolution;

                     if (potential_rect_opcode_px_coord.x >= 0.0 && potential_rect_opcode_px_coord.x < pxos_resolution.x &&
                        potential_rect_opcode_px_coord.y >= 0.0 && potential_rect_opcode_px_coord.y < pxos_resolution.y) {

                        vec4 check_rect_data = texture(px_buffer, potential_rect_opcode_uv);
                        if (abs(check_rect_data.r - PX_DRAW_RECT_ID) < 0.001) {
                            float rect_width = floor(check_rect_data.g * 255.0);
                            float rect_height = floor(check_rect_data.b * 255.0);
                            
                            rect_width = min(rect_width, MAX_RECT_DIMENSION);
                            rect_height = min(rect_height, MAX_RECT_DIMENSION);

                            if (is_in_rect(current_px_coord, potential_rect_opcode_px_coord, vec2(rect_width, rect_height))) {
                                out_color = vec4(0.0, 0.0, 1.0, 1.0);
                                drawn_by_self_rect = true;
                                break;
                            }
                        }
                    }
                }
                if (drawn_by_self_rect) {
                    break;
                }
            }
        }
        else if (abs(opcode_id - PX_COPY_REGION_ID) < 0.001) {
            bool drawn_by_self_copy = false;
            for (float y_k = -COPY_CHECK_NEIGHBORHOOD; y_k <= 0.0; y_k += 1.0) {
                for (float x_k = -COPY_CHECK_NEIGHBORHOOD; x_k <= 0.0; x_k += 1.0) {
                    vec2 potential_copy_opcode_px_coord = current_px_coord + vec2(x_k, y_k);
                    vec2 potential_copy_opcode_uv = potential_copy_opcode_px_coord / pxos_resolution;

                    if (potential_copy_opcode_px_coord.x >= 0.0 && potential_copy_opcode_px_coord.x < pxos_resolution.x &&
                        potential_copy_opcode_px_coord.y >= 0.0 && potential_copy_opcode_px_coord.y < pxos_resolution.y) {

                        vec4 check_copy_data = texture(px_buffer, potential_copy_opcode_uv);
                        if (abs(check_copy_data.r - PX_COPY_REGION_ID) < 0.001) {
                            float src_offset_x = floor(check_copy_data.g * 255.0);
                            float src_offset_y = floor(check_copy_data.b * 255.0);
                            
                            src_offset_x = (src_offset_x / 255.0) * (2.0 * MAX_RECT_DIMENSION) - MAX_RECT_DIMENSION;
                            src_offset_y = (src_offset_y / 255.0) * (2.0 * MAX_RECT_DIMENSION) - MAX_RECT_DIMENSION;


                            if (is_in_rect(current_px_coord, potential_copy_opcode_px_coord, vec2(COPY_REGION_WIDTH, COPY_REGION_HEIGHT))) {
                                vec2 local_dest_coord = current_px_coord - potential_copy_opcode_px_coord;
                                vec2 source_px_coord = potential_copy_opcode_px_coord + vec2(src_offset_x, src_offset_y) + local_dest_coord;
                                vec2 source_uv = source_px_coord / pxos_resolution;

                                out_color = texture(px_buffer, source_uv);
                                drawn_by_self_copy = true;
                                break;
                            }
                        }
                    }
                }
                if (drawn_by_self_copy) {
                    break;
                }
            }
        }
        else if (abs(opcode_id - PX_READ_DATA_TO_COLOR_ID) < 0.001) {
            out_color = texture(px_data_read_buffer, uv_normalized);
        }
    }

    COLOR = out_color;
}