use std::fs;
use std::io::prelude::*;
//use std::io;
use base64::{engine::general_purpose::STANDARD, Engine as _};
use flate2::read::ZlibDecoder;
//use json;
use serde::{Deserialize, Serialize};
use serde_json;
//use flate2::read::ZlibDecoder;
//use serde_json::Value;
//use std::io::Read;

#[derive(Serialize, Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct V2 {
    x: f32,
    y: f32,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(rename_all = "lowercase")]
enum Quality {
    Normal,
    Uncommon,
    Rare,
    Epic,
    Legendary,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct Signal {
    name: String,
    quality: Quality,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct Icon {
    signal: Signal,
    index: u8,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct InInventory {
    inventory: u8,
    stack: u8,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct Item2 {
    in_inventory: Vec<InInventory>,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct Item {
    id: Signal,
    items: Item2,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct Entity {
    entity_number: u32,
    name: String,
    position: V2,
    #[serde(default)]
    direction: u8,
    #[serde(default)]
    mirror: bool,
    quality: Quality,
    recipe: String,
    recipe_quality: Quality,
    items: Vec<Item>,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct Blueprint {
    #[serde(rename = "snap-to-grid")]
    snap_to_grid: V2,
    #[serde(rename = "absolute-snapping")]
    absolute_snapping: bool,
    #[serde(rename = "position-relative-to-grid")]
    position_relative_to_grid: V2,

    icons: Vec<Icon>,
    entities: Vec<Entity>,
    item: String,
    version: u64,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct BlueprintBase {
    blueprint: Blueprint,
}

fn main() {
    // Read the file content
    let content = fs::read_to_string("../../ex_bp.txt").expect("Failed to read file");

    // Remove the first character and trim trailing whitespace
    let trimmed_content = content[1..].trim();

    // Decode the Base64 string
    let decoded = STANDARD.decode(trimmed_content).expect("Failed to decode Base64");

    // Decompress using zlib
    let mut decoder = ZlibDecoder::new(&decoded[..]);
    let mut uncompressed = String::new();
    decoder.read_to_string(&mut uncompressed).expect("Failed to decode zlib");

    // Parse JSON
    let blueprint: BlueprintBase = serde_json::from_str(&uncompressed).expect("Failed to parse JSON");
    println!("{:#?}", blueprint);
    //let json_value = json::parse(&uncompressed).expect("Failed to parse JSON");
    //let json_value = json::parse(&j).expect("Failed to parse JSON");

    // Print the result
    //println!("{:#?}", json_value);
		println!("Hello, World")
}
