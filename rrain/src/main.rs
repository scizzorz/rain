
use std::env;
use std::fs::File;
use std::io::Read;

mod lexer;

mod parser;

fn main() {
    let args: Vec<String> = env::args().collect();

    use std::io::{self};

    let mut buffer: String = String::new();
    match args.len() {
        2 => {
            File::open(&args[1]).expect("File doesn't exist")
                .read_to_string(&mut buffer).expect("File can't be read");
        }
        _ => {
            io::stdin().read_to_string(&mut buffer).expect("Couldn't read stdin");
        }
    };

    match lexer::lex(&buffer) {
        Ok(tokens) => {
            println!("tokens {:?}", tokens);
            let mut token_stream = tokens.iter().peekable();
            println!("ast {:?}", parser::parse(&mut token_stream));
            if token_stream.peek().is_some() {
                println!("LEFTOVER");
                for token in token_stream {
                    println!("{:?}", token)
                };
            }
        }
        Err(s) => {
            println!("Lexing error: {}", s);
        }
    }
}
