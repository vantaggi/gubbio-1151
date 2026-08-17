#!/usr/bin/env python3
"""
Map Exporter: Converte matrici di collisione Tiled (.json o .csv) in header C++ constexpr per Butano Engine.
"""
import json
import sys
import os

def export_map_header(json_file: str, output_header: str, variable_name: str = "COLLISION_MAP"):
    if not os.path.exists(json_file):
        print(f"Errore: File '{json_file}' non trovato.", file=sys.stderr)
        sys.exit(1)

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Prende il layer delle collisioni
    collision_layer = None
    for layer in data.get('layers', []):
        if layer.get('name', '').lower() in ['collision', 'collisions', 'collisioni']:
            collision_layer = layer
            break
    
    if not collision_layer:
        collision_layer = data['layers'][0]
    
    width = collision_layer['width']
    height = collision_layer['height']
    raw_data = collision_layer['data']

    guard_name = os.path.basename(output_header).replace('.', '_').upper()

    os.makedirs(os.path.dirname(os.path.abspath(output_header)), exist_ok=True)
    with open(output_header, 'w', encoding='utf-8') as out:
        out.write(f"// Generato automaticamente da map_exporter.py per Gubbio 1151\n")
        out.write(f"#ifndef {guard_name}\n")
        out.write(f"#define {guard_name}\n\n")
        out.write(f"#include <stdint.h>\n\n")
        out.write(f"namespace gubbio::maps {{\n")
        out.write(f"    constexpr int MAP_WIDTH = {width};\n")
        out.write(f"    constexpr int MAP_HEIGHT = {height};\n\n")
        out.write(f"    constexpr uint8_t {variable_name}[{width * height}] = {{\n        ")
        
        for i, val in enumerate(raw_data):
            out.write(f"{int(val)}, ")
            if (i + 1) % width == 0 and (i + 1) < len(raw_data):
                out.write("\n        ")
        
        out.write("\n    };\n")
        out.write(f"}} // namespace gubbio::maps\n\n")
        out.write(f"#endif // {guard_name}\n")
    
    print(f"[*] Header generato con successo: {output_header} ({width}x{height} tile, {len(raw_data)} bytes).")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        export_map_header(sys.argv[1], sys.argv[2])
    else:
        print("Uso: python map_exporter.py <map_file.json> <output_header.h> [var_name]")
