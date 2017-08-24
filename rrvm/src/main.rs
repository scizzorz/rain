use std::env;
use std::os::raw::c_void;

struct R_item {
    hash: u64,
    key: R_box,
    val: R_box,
}

struct R_table {
    cur: u32,
    max: u32,
    items: Vec<R_item>,
}

enum R_op {
    U32(u32),
    I32(i32),
}

enum R_box_contents {
    U64(u64),
    I64(i64),
    F64(f64),
    Str(String),
    RTable(R_table),
    Ptr(c_void),
}

struct R_box {
    typ: char,
    size: i32,
    contents: R_box_contents,
    meta: Option<Box<R_box>>,
}

fn empty_rbox() -> R_box {
    R_box {
        typ: '\0',
        size: 0,
        contents: R_box_contents::U64(0),
        meta: None,
    }
}

struct R_header {
    rain: [char; 4],
    num_consts: u32,
    num_instrs: u32,
    num_strings: u32,
}

struct R_frame {
    return_to: u32,
    base_ptr: u32,
    argc: u32,
    scope: R_box,
    ret: R_box,
}

struct R_catch {
    instr_ptr: u32,
    stack_ptr: u32,
    frame_ptr: u32,
}

struct R_vm {
    instr_ptr: u32,
    num_consts: u32,
    num_instrs: u32,
    num_strings: u32,

    stack_ptr: u32,
    stack_size: u32,

    catch_ptr: u32,
    catch_size: u32,

    frame_ptr: u32,
    frame_size: u32,

    strings: Vec<String>,
    consts: R_box,
    instrs: R_op,
    stack: Vec<R_box>,
    frames: Vec<R_frame>,
    frame: Option<R_frame>,
    catches: Vec<R_catch>,
}

fn vm_new() -> R_vm {
    R_vm {
        num_consts: 0,
        num_instrs: 0,
        num_strings: 0,

        instr_ptr: std::u32::MAX - 1,
        stack_ptr: 0,
        catch_ptr: 0,
        frame_ptr: 0,

        stack_size: 10,
        catch_size: 10,
        frame_size: 10,

        consts: empty_rbox(),
        instrs: R_op::U32(0),
        strings: Vec::new(),

        stack: Vec::new(),
        frames: Vec::new(),
        frame: None,
        catches: Vec::new(),
    }
}

fn vm_import(vm: &R_vm, s: &String) {
    println!("importing");
}

fn vm_run(vm: &R_vm) {
    println!("running");
}

fn main() {
    let args: Vec<String> = env::args().collect();

    match args.len() {
        2 => run_vm(&args[1]),
        _ => print_usage(&args[0]),
    }
}

fn print_usage(s: &String) {
    println!("Usage: {} FILE\n", s)
}

fn run_vm(s: &String) {
    println!("starting vm...");
    let vm = vm_new();
    println!("importing {}...", s);
    vm_import(&vm, s);
    println!("running {}...", s);
    vm_run(&vm);
}
